#!/usr/bin/env python3
"""
Port Extractor - Gets real destination ports from /proc/net/tcp
This complements eBPF/auditd collectors that don't extract ports
"""
import re
import logging
from typing import Dict, Optional, Tuple
from collections import defaultdict

logger = logging.getLogger('security_agent.port_extractor')


class PortExtractor:
    """Extract real destination ports from /proc/net/tcp"""
    
    def __init__(self):
        self.port_cache: Dict[int, Tuple[str, int]] = {}  # pid -> (dest_ip, dest_port)
        self.cache_timeout = 2.0  # Cache for 2 seconds
        self.last_update = 0.0
        self._connection_map: Dict[int, Tuple[str, int]] = {}  # inode -> (dest_ip, dest_port)
    
    def _parse_proc_net_tcp(self) -> Dict[int, Tuple[str, int]]:
        """Parse /proc/net/tcp to get inode -> (dest_ip, dest_port) mapping"""
        connection_map = {}
        
        try:
            with open('/proc/net/tcp', 'r') as f:
                for line in f:
                    # Format: sl local_address rem_address st tx_queue rx_queue tr tm->when retrnsmt uid timeout inode
                    # Example: 0: 0100007F:1F90 00000000:0000 0A 00000000:00000000 00:00000000 00000000  1000        0 12345 1 0000000000000000 100 0 0 10 0
                    parts = line.strip().split()
                    if len(parts) < 10:
                        continue
                    
                    # Extract remote address (rem_address) - format: AABBCCDD:PORT (hex)
                    rem_addr = parts[2]  # e.g., "0100007F:1F90"
                    if ':' in rem_addr:
                        addr_hex, port_hex = rem_addr.split(':')
                        try:
                            # Convert hex to int
                            port = int(port_hex, 16)
                            # Convert IP from hex (little-endian)
                            ip_bytes = bytes.fromhex(addr_hex)
                            ip = '.'.join(str(b) for b in reversed(ip_bytes))
                            
                            # Get inode - it's usually the 10th field (index 9), but check for state first
                            # State is in parts[3] (0A = ESTABLISHED)
                            state = parts[3]
                            # Inode is typically the 10th field, but let's be more robust
                            inode_idx = 9
                            if len(parts) > inode_idx:
                                inode = int(parts[inode_idx])
                                
                                # Only track ESTABLISHED connections (state 01 = ESTABLISHED)
                                # State codes: 01=ESTABLISHED, 02=SYN_SENT, 03=SYN_RECV, etc.
                                if port > 0 and (state == '01' or state == '0A'):  # ESTABLISHED
                                    connection_map[inode] = (ip, port)
                                    logger.debug(f"Found connection: inode={inode}, {ip}:{port}, state={state}")
                        except (ValueError, IndexError) as e:
                            logger.debug(f"Error parsing /proc/net/tcp line: {e}")
                            continue
        except (FileNotFoundError, PermissionError) as e:
            logger.warning(f"Could not read /proc/net/tcp: {e}")
        
        return connection_map
    
    def _get_pid_inodes(self, pid: int) -> list:
        """Get socket inodes for a PID from /proc/PID/fd"""
        inodes = []
        try:
            fd_dir = f'/proc/{pid}/fd'
            import os
            if os.path.exists(fd_dir):
                for fd in os.listdir(fd_dir):
                    try:
                        link = os.readlink(f'{fd_dir}/{fd}')
                        # Socket links look like: socket:[12345]
                        if link.startswith('socket:['):
                            inode = int(link[8:-1])
                            inodes.append(inode)
                    except (OSError, ValueError):
                        continue
        except (OSError, PermissionError):
            pass
        
        return inodes
    
    def get_destination(self, pid: int) -> Optional[Tuple[str, int]]:
        """
        Get destination IP and port for a PID
        
        Returns:
            (dest_ip, dest_port) tuple or None if not found
        """
        import time
        
        # Update cache if stale
        current_time = time.time()
        if current_time - self.last_update > self.cache_timeout:
            self._connection_map = self._parse_proc_net_tcp()
            self.last_update = current_time
            self.port_cache.clear()  # Clear old cache
        
        # Check cache first
        if pid in self.port_cache:
            return self.port_cache[pid]
        
        # Get inodes for this PID
        inodes = self._get_pid_inodes(pid)
        
        # Find matching connection
        for inode in inodes:
            if inode in self._connection_map:
                dest_ip, dest_port = self._connection_map[inode]
                # Cache it
                self.port_cache[pid] = (dest_ip, dest_port)
                logger.debug(f"Found real port for PID {pid}: {dest_ip}:{dest_port} (inode={inode})")
                return (dest_ip, dest_port)
        
        return None
    
    def get_destination_port(self, pid: int) -> int:
        """Get destination port for a PID, returns 0 if not found"""
        result = self.get_destination(pid)
        if result:
            return result[1]  # Return port
        return 0
