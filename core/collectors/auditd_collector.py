"""
Auditd collector - implements BaseCollector interface directly
"""
import os
import re
import threading
import time
from typing import Callable, Dict, Any, Optional
import logging

from .base import BaseCollector, SyscallEvent

logger = logging.getLogger('security_agent.collector.auditd')


class AuditdCollector(BaseCollector):
    """Auditd-based syscall collector"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.audit_log_path = self.config.get('audit_log_path', '/var/log/audit/audit.log')
        self.thread: Optional[threading.Thread] = None
        
        # Regex to extract basic fields from auditd SYSCALL line
        # Matches both numeric and named syscall tokens
        # Example numeric: syscall=59; named: syscall=execve
        self.syscall_re = re.compile(
            r"type=SYSCALL .*?syscall=([^\s]+).*?pid=(\d+).*?uid=(\d+).*?comm=\"([^\"]*)\".*?exe=\"([^\"]*)\""
        )
        
        # Simple syscall number to name map (subset); eBPF path has full map
        # Network syscalls are critical for attack detection
        self.syscall_num_to_name = {
            '59': 'execve', '322': 'execveat', '57': 'fork', '56': 'clone', '58': 'vfork',
            '257': 'openat', '2': 'open', '3': 'close', '0': 'read', '1': 'write',
            '101': 'ptrace', '160': 'mount', '166': 'umount2', '105': 'setuid', '106': 'setgid',
            '90': 'chmod', '92': 'chown', 
            # Network syscalls (critical for attack detection)
            '41': 'socket', '42': 'connect', '43': 'accept', '49': 'bind', '50': 'listen',
            '44': 'sendto', '45': 'recvfrom', '46': 'sendmsg', '47': 'recvmsg'
        }
    
    def is_available(self) -> bool:
        """Check if auditd is available"""
        return os.path.exists(self.audit_log_path) and os.access(self.audit_log_path, os.R_OK)
    
    def start_monitoring(self, event_callback: Callable[[SyscallEvent], None]) -> bool:
        """Start auditd monitoring"""
        if not self.is_available():
            logger.error(f"Audit log not available: {self.audit_log_path}")
            return False
        
        try:
            self.running = True
            self.thread = threading.Thread(target=self._tail_loop, args=(event_callback,), daemon=True)
            self.thread.start()
            logger.info(f"✅ Auditd collector started monitoring {self.audit_log_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to start auditd collector: {e}")
            self.running = False
            return False
    
    def stop_monitoring(self) -> None:
        """Stop auditd monitoring"""
        self.running = False
        # Thread is daemon; it will exit shortly
    
    def _tail_loop(self, event_callback: Callable[[SyscallEvent], None]):
        """Tail audit log and emit events"""
        try:
            logger.info(f"Starting auditd tail loop for {self.audit_log_path}")
            with open(self.audit_log_path, 'r', errors='ignore') as f:
                # Seek to end for live tail
                f.seek(0, os.SEEK_END)
                event_count = 0
                while self.running:
                    line = f.readline()
                    if not line:
                        time.sleep(0.1)
                        continue
                    
                    # Only process SYSCALL lines
                    if 'type=SYSCALL' not in line:
                        continue
                    
                    m = self.syscall_re.search(line)
                    if not m:
                        logger.debug(f"Failed to parse auditd line: {line[:100]}")
                        continue
                    
                    syscall_token, pid_str, uid_str, comm, exe = m.groups()
                    pid = int(pid_str)
                    uid = int(uid_str)
                    
                    # Prefer named token; if numeric, map best-effort
                    if syscall_token.isdigit():
                        syscall_name = self.syscall_num_to_name.get(syscall_token, f'syscall_{syscall_token}')
                    else:
                        syscall_name = syscall_token
                    
                    # IMPROVEMENT: Handle sudo-wrapped processes
                    # If comm is "sudo" but exe contains python3, use python3 as the process name
                    # This allows detection of attacks run via sudo python3 script.py
                    resolved_comm = comm
                    if comm == 'sudo' and exe and 'python' in exe.lower():
                        # Extract python3 from exe path (e.g., /usr/bin/python3.10 -> python3)
                        resolved_comm = 'python3'
                        logger.debug(f"Resolved sudo process: PID={pid} exe={exe} -> comm={resolved_comm}")
                    elif comm == 'sudo' and exe:
                        # For other sudo processes, try to infer from exe
                        exe_basename = os.path.basename(exe) if exe else ''
                        if exe_basename and exe_basename != 'sudo':
                            resolved_comm = exe_basename
                            logger.debug(f"Resolved sudo process: PID={pid} exe={exe} -> comm={resolved_comm}")
                    
                    # Log network syscalls for debugging
                    network_syscalls = ['socket', 'connect', 'bind', 'accept', 'sendto', 'sendmsg']
                    is_network = syscall_name.lower() in network_syscalls
                    if is_network or event_count < 10:
                        logger.info(f"📥 auditd event: PID={pid} syscall={syscall_name} comm={resolved_comm} (original={comm}) exe={exe}")
                    
                    # Create SyscallEvent with resolved comm
                    event = SyscallEvent(
                        pid=pid,
                        syscall=syscall_name,
                        uid=uid,
                        comm=resolved_comm,  # Use resolved comm instead of original
                        exe=exe,
                        timestamp=time.time(),
                        event_info={'source': 'auditd', 'raw_line': line[:200], 'original_comm': comm}
                    )
                    
                    try:
                        event_callback(event)
                        event_count += 1
                        if event_count % 100 == 0:
                            logger.debug(f"Processed {event_count} auditd events")
                    except Exception as e:
                        # Ignore callback errors to keep tailing
                        logger.warning(f"Callback error: {e}")
        except Exception as e:
            logger.error(f"Error in auditd tail loop: {e}", exc_info=True)
            self.running = False
