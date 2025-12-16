#!/usr/bin/env python3
"""
Lightweight eBPF Port Extractor - Extracts real destination ports from connect syscalls
This is OPTIONAL and only used for C2 detection - doesn't replace auditd collector
"""
import logging
import time
from typing import Optional, Tuple, Dict
from collections import defaultdict

logger = logging.getLogger('security_agent.ebpf_port')

try:
    from bcc import BPF
    BCC_AVAILABLE = True
except ImportError:
    BCC_AVAILABLE = False
    BPF = None


class EBPFPortExtractor:
    """
    Lightweight eBPF helper to extract real destination ports from connect syscalls
    This complements auditd collector - doesn't replace it
    """
    
    def __init__(self):
        self.bpf = None
        self.port_cache: Dict[int, Tuple[str, int]] = {}  # pid -> (dest_ip, dest_port)
        self.cache_timeout = 5.0  # Cache ports for 5 seconds
        self.last_cleanup = time.time()
        self.enabled = False
        
        if not BCC_AVAILABLE:
            logger.warning("BCC not available - eBPF port extraction disabled")
            return
        
        try:
            self._load_ebpf_program()
            if self.bpf is not None:
                self.enabled = True
                logger.warning("✅ eBPF port extractor loaded successfully - REAL ports available for C2 detection!")
            else:
                logger.warning("eBPF program loaded but bpf is None - kprobe attachment may have failed")
        except Exception as e:
            logger.warning(f"Failed to load eBPF port extractor: {e} (will use simulated ports)", exc_info=True)
            self.bpf = None
            self.enabled = False
    
    def _load_ebpf_program(self):
        """Load minimal eBPF program to extract ports from connect syscalls"""
        # Try tracepoint first (more reliable), fallback to kprobe
        ebpf_code = """
#include <uapi/linux/ptrace.h>
#include <net/sock.h>
#include <linux/socket.h>
#include <linux/in.h>
#include <linux/in6.h>

// Event structure
struct port_event {
    u32 pid;
    u32 dest_ip;  // IPv4 address in host byte order
    u16 dest_port;  // Port in host byte order
    u8 family;  // Address family (AF_INET, AF_INET6)
};

// Map to store recent ports (pid -> port_event)
BPF_HASH(port_map, u32, struct port_event);

// Helper function to extract port from sockaddr
static int extract_port_info(u32 pid, struct sockaddr *addr, int addrlen) {
    if (addrlen < 2 || addr == 0) {
        return 0;  // Invalid arguments
    }
    
    // Read address family
    u16 family = 0;
    if (bpf_probe_read_user(&family, sizeof(family), &addr->sa_family) != 0) {
        return 0;  // Failed to read family
    }
    
    struct port_event event = {};
    event.pid = pid;
    event.family = (u8)family;
    
    if (family == AF_INET && addrlen >= sizeof(struct sockaddr_in)) {
        // IPv4
        struct sockaddr_in sa;
        if (bpf_probe_read_user(&sa, sizeof(sa), addr) == 0) {
            event.dest_ip = bpf_ntohl(sa.sin_addr.s_addr);
            event.dest_port = bpf_ntohs(sa.sin_port);
            port_map.update(&pid, &event);
            return 1;  // Success
        }
    } else if (family == AF_INET6 && addrlen >= sizeof(struct sockaddr_in6)) {
        // IPv6
        struct sockaddr_in6 sa6;
        if (bpf_probe_read_user(&sa6, sizeof(sa6), addr) == 0) {
            event.dest_port = bpf_ntohs(sa6.sin6_port);
            event.dest_ip = 0;  // IPv6 placeholder
            port_map.update(&pid, &event);
            return 1;  // Success
        }
    }
    
    return 0;
}

// Kprobe for connect syscall
int trace_connect(struct pt_regs *ctx) {
    u64 id = bpf_get_current_pid_tgid();
    u32 pid = id >> 32;
    
    // Get syscall arguments: sockfd (arg1), addr (arg2), addrlen (arg3)
    int sockfd = (int)PT_REGS_PARM1(ctx);
    struct sockaddr *addr = (struct sockaddr *)PT_REGS_PARM2(ctx);
    int addrlen = (int)PT_REGS_PARM3(ctx);
    
    extract_port_info(pid, addr, addrlen);
    return 0;
}
"""
        try:
            # Suppress stderr during compilation (macro warnings are harmless)
            import os
            import sys
            devnull = open(os.devnull, 'w')
            old_stderr = sys.stderr
            sys.stderr = devnull
            
            try:
                self.bpf = BPF(text=ebpf_code)
                # Try tracepoint first (more reliable), then kprobe
                attached = False
                attach_errors = []
                
                # Method 1: Try tracepoint (syscalls:sys_enter_connect)
                try:
                    self.bpf.attach_tracepoint(tp="syscalls:sys_enter_connect", fn_name="trace_connect")
                    logger.warning("✅ Attached tracepoint syscalls:sys_enter_connect")
                    attached = True
                except Exception as e:
                    attach_errors.append(f"tracepoint: {e}")
                    logger.debug(f"Tracepoint not available: {e}")
                
                # Method 2: Try kprobe if tracepoint failed
                if not attached:
                    event_names = ["__x64_sys_connect", "__sys_connect", "sys_connect"]
                    for event_name in event_names:
                        try:
                            self.bpf.attach_kprobe(event=event_name, fn_name="trace_connect")
                            logger.warning(f"✅ Attached kprobe to {event_name}")
                            attached = True
                            break
                        except Exception as e:
                            attach_error = str(e)
                            attach_errors.append(f"{event_name}: {attach_error}")
                            continue
                
                if not attached:
                    error_msg = f"Could not attach to connect syscall. Errors: {'; '.join(attach_errors)}"
                    logger.error(error_msg)
                    self.bpf = None
                    return
                
                # Verify it's working with a test
                logger.warning("eBPF port extractor ready - will capture ports on next connect() calls")
            finally:
                sys.stderr.close()
                sys.stderr = old_stderr
                devnull.close()
        except Exception as e:
            logger.warning(f"eBPF program load error: {e}")
            raise
    
    def get_destination(self, pid: int) -> Optional[Tuple[str, int]]:
        """
        Get destination IP and port for a PID from eBPF map
        
        Returns:
            (dest_ip, dest_port) tuple or None if not found
        """
        if not self.enabled or not self.bpf:
            return None
        
        # Cleanup old cache entries
        current_time = time.time()
        if current_time - self.last_cleanup > self.cache_timeout:
            self.port_cache.clear()
            self.last_cleanup = current_time
        
        # Check cache first
        if pid in self.port_cache:
            return self.port_cache[pid]
        
        try:
            # Get port from eBPF map
            port_map = self.bpf.get_table("port_map")
            
            # Try to get by PID
            pid_key = port_map.Key(pid)
            event = port_map[pid_key]
            
            if event:
                # Convert IP from uint32 to dotted quad
                ip_int = event.dest_ip
                if ip_int > 0:
                    ip = f"{(ip_int >> 24) & 0xFF}.{(ip_int >> 16) & 0xFF}.{(ip_int >> 8) & 0xFF}.{ip_int & 0xFF}"
                else:
                    ip = "0.0.0.0"  # IPv6 or unknown
                
                port = event.dest_port
                
                if port > 0:
                    result = (ip, port)
                    self.port_cache[pid] = result
                    logger.warning(f"✅ eBPF extracted REAL port for PID {pid}: {ip}:{port}")
                    return result
            else:
                # Try iterating to find the PID (fallback)
                for k, v in port_map.items():
                    if k.value == pid:
                        ip_int = v.dest_ip
                        if ip_int > 0:
                            ip = f"{(ip_int >> 24) & 0xFF}.{(ip_int >> 16) & 0xFF}.{(ip_int >> 8) & 0xFF}.{ip_int & 0xFF}"
                        else:
                            ip = "0.0.0.0"
                        port = v.dest_port
                        if port > 0:
                            result = (ip, port)
                            self.port_cache[pid] = result
                            logger.warning(f"✅ eBPF extracted REAL port for PID {pid} (via iteration): {ip}:{port}")
                            return result
        except KeyError:
            # PID not in map - that's okay, connection might not have happened yet
            pass
        except Exception as e:
            logger.debug(f"Error reading eBPF port map for PID {pid}: {e}")
        
        return None
    
    def get_destination_port(self, pid: int) -> int:
        """Get destination port for a PID, returns 0 if not found"""
        result = self.get_destination(pid)
        if result:
            return result[1]  # Return port
        return 0
    
    def cleanup(self):
        """Cleanup eBPF resources"""
        if self.bpf:
            try:
                # Detach kprobes
                self.bpf.detach_kprobe(event="__x64_sys_connect", fn_name="kprobe__sys_connect")
            except:
                pass
            self.bpf = None
        self.enabled = False
