#!/usr/bin/env python3
"""
Connection Pattern Analyzer
============================

Detects suspicious network connection patterns including:
- C2 beaconing (regular intervals)
- Port scanning (rapid connections to multiple ports)
- Data exfiltration (large uploads)
- Unusual destinations

Improves MITRE ATT&CK coverage for:
- T1071: Application Layer Protocol (C2)
- T1041: Exfiltration Over C2 Channel
- T1046: Network Service Scanning

Author: Likitha Shankar
"""

import time
from collections import defaultdict, deque
from typing import Dict, List, Tuple, Optional
import statistics
import logging

logger = logging.getLogger('security_agent.connection_pattern')


class ConnectionPatternAnalyzer:
    """
    Analyzes network connection patterns to detect:
    - C2 beaconing (regular communication intervals)
    - Port scanning (rapid connections to many ports)
    - Data exfiltration patterns
    """
    
    def __init__(self, config: Dict = None):
        """
        Initialize connection pattern analyzer
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        
        # Connection tracking per process (by PID)
        self.connection_history = defaultdict(lambda: deque(maxlen=100))
        
        # Connection tracking by process name + IP (for C2 beaconing when PID changes)
        # This helps track connections from short-lived processes
        self.connection_history_by_name = defaultdict(lambda: defaultdict(lambda: deque(maxlen=100)))  # process_name -> dest_ip -> connections
        
        # Port scanning detection
        self.port_access_history = defaultdict(set)  # pid -> set of ports
        self.port_access_history_by_name = defaultdict(lambda: defaultdict(set))  # process_name -> dest_ip -> set of ports
        
        # Beaconing detection parameters (optimized for better detection)
        self.beacon_threshold_variance = self.config.get('beacon_variance_threshold', 10.0)  # Increased to 10.0s for better C2 detection
        self.min_connections_for_beacon = self.config.get('min_connections_for_beacon', 3)  # Minimum 3 connections
        self.min_beacon_interval = self.config.get('min_beacon_interval', 1.0)  # Lowered to 1.0 seconds for better detection
        
        # Port scanning parameters (balanced for detection vs false positives)
        # Lowered threshold back to 5 for better attack detection (can be tuned via config)
        self.port_scan_threshold = self.config.get('port_scan_threshold', 5)  # unique ports (5 for better detection)
        self.port_scan_timeframe = self.config.get('port_scan_timeframe', 60)  # seconds (60s window for detection)
        
        # Whitelist of legitimate processes that commonly connect to multiple ports
        # These are system/daemon processes that shouldn't trigger port scan alerts
        self.whitelisted_processes = {
            'systemd', 'systemctl', 'groupadd', 'useradd', 'usermod',
            'flb-out-stackdr', 'fluent-bit', 'fluentd',
            'sshd', 'rsyslog', 'syslog', 'journald',
            'dnsmasq', 'resolvconf', 'networkd', 'NetworkManager',
            'apt', 'apt-get', 'yum', 'dnf', 'zypper', 'pacman',
            'curl', 'wget', 'ping', 'nslookup', 'dig',
            'docker', 'containerd', 'kubelet', 'kube-proxy'
        }
        
        # Data transfer tracking
        self.bytes_sent = defaultdict(int)
        self.bytes_received = defaultdict(int)
        self.exfiltration_threshold = self.config.get('exfiltration_threshold', 100 * 1024 * 1024)  # 100 MB
        
        # Statistics
        self.stats = {
            'beacons_detected': 0,
            'port_scans_detected': 0,
            'exfiltrations_detected': 0,
            'total_connections_analyzed': 0
        }
    
    def analyze_connection(self, pid: int, dest_ip: str, dest_port: int, 
                          timestamp: float = None, process_name: str = None) -> Optional[Dict]:
        """
        Analyze a network connection for suspicious patterns
        
        Args:
            pid: Process ID
            dest_ip: Destination IP address
            dest_port: Destination port
            timestamp: Connection timestamp (default: current time)
            process_name: Process name (for tracking across PID changes)
        
        Returns:
            Detection result if suspicious, None otherwise
        """
        if timestamp is None:
            timestamp = time.time()
        
        # Skip detection for whitelisted legitimate processes
        if process_name and process_name.lower() in [p.lower() for p in self.whitelisted_processes]:
            return None
        
        self.stats['total_connections_analyzed'] += 1
        
        # Record connection by PID
        connection_info = {
            'dest': f"{dest_ip}:{dest_port}",
            'ip': dest_ip,
            'port': dest_port,
            'time': timestamp,
            'pid': pid
        }
        self.connection_history[pid].append(connection_info)
        self.port_access_history[pid].add(dest_port)
        
        # Also track by process name + IP (for C2 beaconing when PID changes)
        if process_name:
            # Clean process name (remove parentheses if present)
            clean_name = process_name
            if process_name.startswith('(') and process_name.endswith(')'):
                clean_name = process_name[1:-1]
            
            self.connection_history_by_name[clean_name][dest_ip].append(connection_info)
            self.port_access_history_by_name[clean_name][dest_ip].add(dest_port)
            total_conns = len(self.connection_history_by_name[clean_name][dest_ip])
            logger.warning(f"🔍 Tracked connection: process={clean_name}, dest={dest_ip}:{dest_port}, total_connections={total_conns}")
            
            # Log when we have enough connections for C2 detection
            if total_conns >= self.min_connections_for_beacon:
                logger.warning(f"🔍 Process {clean_name} has {total_conns} connections to {dest_ip}:{dest_port} - checking for C2...")
        
        # Check for beaconing (try both PID and process name tracking)
        beacon_result = self._detect_beaconing(pid)
        if not beacon_result and process_name:
            # Try detecting by process name (for short-lived processes)
            beacon_result = self._detect_beaconing_by_name(process_name, dest_ip)
        if beacon_result:
            self.stats['beacons_detected'] += 1
            logger.warning(f"✅ C2 BEACONING RETURNED from analyze_connection: {beacon_result.get('type')} for PID {pid}")
            return beacon_result
        else:
            # Log why C2 wasn't detected (WARNING level so it's visible)
            pid_conns = len(self.connection_history[pid]) if pid in self.connection_history else 0
            name_conns = len(self.connection_history_by_name.get(process_name, {}).get(dest_ip, [])) if process_name else 0
            if name_conns >= 3 or pid_conns >= 3:
                logger.warning(f"🔍 No C2 detected yet: PID {pid} has {pid_conns} connections, {process_name}->{dest_ip} has {name_conns} connections (should check intervals)")
        
        # Check for port scanning (try both PID and process name tracking)
        scan_result = self._detect_port_scanning(pid, timestamp)
        if not scan_result and process_name:
            # Try detecting by process name (for short-lived processes)
            scan_result = self._detect_port_scanning_by_name(process_name, dest_ip, timestamp)
        if scan_result:
            self.stats['port_scans_detected'] += 1
            return scan_result
        
        return None
    
    def _detect_beaconing(self, pid: int) -> Optional[Dict]:
        """
        Detect C2 beaconing patterns (regular intervals to SAME port)
        
        C2 malware often "calls home" at regular intervals (e.g., every 60 seconds)
        IMPORTANT: C2 beaconing requires connections to the SAME destination port
        """
        all_connections = list(self.connection_history[pid])
        
        logger.warning(f"🔍 _detect_beaconing called for PID {pid}: {len(all_connections)} total connections")
        
        if len(all_connections) < self.min_connections_for_beacon:
            logger.warning(f"🔍 Not enough connections for C2: {len(all_connections)} < {self.min_connections_for_beacon}")
            return None
        
        # Group connections by destination (IP:port) to find beaconing patterns
        # C2 beaconing is to the SAME destination port
        connections_by_dest = defaultdict(list)
        for conn in all_connections:
            dest_key = conn['dest']  # "IP:port"
            connections_by_dest[dest_key].append(conn)
        
        # Check each destination for beaconing pattern
        for dest_key, connections in connections_by_dest.items():
            if len(connections) < self.min_connections_for_beacon:
                continue
            
            # Sort by time to ensure correct order
            connections = sorted(connections, key=lambda x: x['time'])
            
            # Calculate time intervals between connections to SAME destination
            intervals = []
            for i in range(1, len(connections)):
                interval = connections[i]['time'] - connections[i-1]['time']
                intervals.append(interval)
            
            if len(intervals) < self.min_connections_for_beacon - 1:
                continue
            
            # Check for regular timing (low variance = beaconing)
            try:
                mean_interval = statistics.mean(intervals)
                
                # Only consider if intervals are reasonably long (>= min_beacon_interval)
                if mean_interval < self.min_beacon_interval:
                    continue
                
                # Calculate variance
                if len(intervals) >= 2:
                    variance = statistics.variance(intervals)
                    stdev = statistics.stdev(intervals)
                    
                    # Low variance indicates regular beaconing
                    # Log debug info for troubleshooting
                    logger.warning(f"🔍 C2 check: dest={dest_key}, connections={len(connections)}, mean_interval={mean_interval:.2f}s, stdev={stdev:.2f}s, threshold={self.beacon_threshold_variance}s, min_interval={self.min_beacon_interval}s")
                    
                    # Check if intervals are regular (low variance) and reasonably spaced
                    if mean_interval >= self.min_beacon_interval:
                        if stdev < self.beacon_threshold_variance:
                            logger.warning(f"✅ C2 BEACONING DETECTED: dest={dest_key}, mean={mean_interval:.1f}s, stdev={stdev:.1f}s, connections={len(connections)}")
                            return {
                                'type': 'C2_BEACONING',
                                'technique': 'T1071',
                                'pid': pid,
                                'mean_interval': mean_interval,
                                'variance': variance,
                                'stdev': stdev,
                                'connections': len(connections),
                                'destination': dest_key,
                                'risk_score': 85,
                                'explanation': f'Regular beaconing detected: {mean_interval:.1f}s intervals (±{stdev:.1f}s) to {dest_key}',
                                'confidence': 0.9,
                                'severity': 'HIGH'
                            }
                        else:
                            logger.warning(f"🔍 C2 NOT detected: stdev={stdev:.2f}s >= threshold {self.beacon_threshold_variance}s (too irregular)")
                    else:
                        logger.warning(f"🔍 C2 NOT detected: mean_interval={mean_interval:.2f}s < min {self.min_beacon_interval}s (too fast)")
            except statistics.StatisticsError as e:
                logger.debug(f"🔍 C2 detection StatisticsError: {e}")
                continue
        
        return None
    
    def _detect_beaconing_by_name(self, process_name: str, dest_ip: str) -> Optional[Dict]:
        """
        Detect C2 beaconing by process name (handles short-lived processes)
        """
        connections = list(self.connection_history_by_name[process_name][dest_ip])
        
        if len(connections) < self.min_connections_for_beacon:
            return None
        
        # Calculate time intervals between connections
        intervals = []
        for i in range(1, len(connections)):
            interval = connections[i]['time'] - connections[i-1]['time']
            intervals.append(interval)
        
        if len(intervals) < self.min_connections_for_beacon - 1:
            return None
        
        # Check for regular timing (low variance = beaconing)
        try:
            mean_interval = statistics.mean(intervals)
            
            # Only consider if intervals are reasonably long (>= min_beacon_interval)
            if mean_interval < self.min_beacon_interval:
                return None
            
            # Calculate variance
            if len(intervals) >= 2:
                variance = statistics.variance(intervals)
                stdev = statistics.stdev(intervals)
                
                # Low variance indicates regular beaconing
                logger.debug(f"🔍 C2 by_name check: process={process_name}, dest_ip={dest_ip}, connections={len(connections)}, mean_interval={mean_interval:.2f}s, stdev={stdev:.2f}s")
                
                if stdev < self.beacon_threshold_variance and mean_interval >= self.min_beacon_interval:
                    logger.warning(f"✅ C2 BEACONING DETECTED (by_name): process={process_name}, mean={mean_interval:.1f}s, stdev={stdev:.1f}s")
                    return {
                        'type': 'C2_BEACONING',
                        'technique': 'T1071',
                        'pid': connections[-1]['pid'],  # Use most recent PID
                        'process_name': process_name,
                        'mean_interval': mean_interval,
                        'variance': variance,
                        'stdev': stdev,
                        'connections': len(connections),
                        'destination': connections[-1]['dest'],
                        'risk_score': 85,
                        'explanation': f'Regular beaconing detected: {mean_interval:.1f}s intervals (±{stdev:.1f}s)',
                        'confidence': 0.9,
                        'severity': 'HIGH'
                    }
                else:
                    logger.debug(f"🔍 C2 by_name NOT detected: stdev={stdev:.2f} >= {self.beacon_threshold_variance} OR mean={mean_interval:.2f} < {self.min_beacon_interval}")
        except statistics.StatisticsError as e:
            logger.debug(f"🔍 C2 by_name StatisticsError: {e}")
            pass
        
        return None
    
    def _detect_port_scanning(self, pid: int, current_time: float) -> Optional[Dict]:
        """
        Detect port scanning (accessing many ports quickly)
        """
        unique_ports = len(self.port_access_history[pid])
        
        if unique_ports < self.port_scan_threshold:
            return None
        
        # Check if this happened in a short timeframe
        connections = list(self.connection_history[pid])
        if not connections:
            return None
        
        # Get time range
        oldest = connections[0]['time']
        newest = connections[-1]['time']
        timeframe = newest - oldest
        
        # Port scan: Many unique ports in short time
        # Also require minimum rate (ports per second) to reduce false positives
        if timeframe < self.port_scan_timeframe and unique_ports >= self.port_scan_threshold:
            ports_per_second = unique_ports / max(timeframe, 1)
            
            # Require minimum rate of 0.1 ports/second (reduces false positives but allows slower scans)
            if ports_per_second < 0.1:
                return None
            
            return {
                'type': 'PORT_SCANNING',
                'technique': 'T1046',
                'pid': pid,
                'unique_ports': unique_ports,
                'timeframe': timeframe,
                'rate': ports_per_second,
                'risk_score': 75,
                'explanation': f'Port scanning: {unique_ports} ports in {timeframe:.1f}s ({ports_per_second:.2f} ports/sec)',
                'confidence': 0.85,
                'severity': 'HIGH'
            }
        
        return None
    
    def _detect_port_scanning_by_name(self, process_name: str, dest_ip: str, current_time: float) -> Optional[Dict]:
        """
        Detect port scanning by process name (handles short-lived processes)
        """
        unique_ports = len(self.port_access_history_by_name[process_name][dest_ip])
        
        if unique_ports < self.port_scan_threshold:
            return None
        
        connections = list(self.connection_history_by_name[process_name][dest_ip])
        if not connections:
            return None
        
        # Get time range
        oldest = connections[0]['time']
        newest = connections[-1]['time']
        timeframe = newest - oldest
        
        # Port scan: Many unique ports in short time
        if timeframe < self.port_scan_timeframe and unique_ports >= self.port_scan_threshold:
            ports_per_second = unique_ports / max(timeframe, 1)
            
            # Require minimum rate of 0.1 ports/second (reduces false positives but allows slower scans)
            if ports_per_second < 0.1:
                return None
            
            return {
                'type': 'PORT_SCANNING',
                'technique': 'T1046',
                'pid': connections[-1]['pid'],  # Use most recent PID
                'process_name': process_name,
                'unique_ports': unique_ports,
                'timeframe': timeframe,
                'rate': ports_per_second,
                'risk_score': 75,
                'explanation': f'Port scanning: {unique_ports} ports in {timeframe:.1f}s ({ports_per_second:.2f} ports/sec)',
                'confidence': 0.85,
                'severity': 'HIGH'
            }
        
        return None
    
    def track_data_transfer(self, pid: int, bytes_sent: int = 0, bytes_received: int = 0) -> Optional[Dict]:
        """
        Track data transfers to detect exfiltration
        
        Args:
            pid: Process ID
            bytes_sent: Bytes sent in this operation
            bytes_received: Bytes received in this operation
        
        Returns:
            Detection result if exfiltration suspected
        """
        self.bytes_sent[pid] += bytes_sent
        self.bytes_received[pid] += bytes_received
        
        # Check for large uploads (potential exfiltration)
        if self.bytes_sent[pid] > self.exfiltration_threshold:
            self.stats['exfiltrations_detected'] += 1
            
            return {
                'type': 'DATA_EXFILTRATION',
                'technique': 'T1041',
                'pid': pid,
                'bytes_sent': self.bytes_sent[pid],
                'bytes_received': self.bytes_received[pid],
                'ratio': self.bytes_sent[pid] / max(self.bytes_received[pid], 1),
                'risk_score': 90,
                'explanation': f'Large data upload: {self.bytes_sent[pid] / (1024*1024):.1f} MB sent',
                'confidence': 0.8,
                'severity': 'CRITICAL'
            }
        
        return None
    
    def get_suspicious_destinations(self, pid: int) -> List[str]:
        """Get list of suspicious destinations for a process"""
        connections = list(self.connection_history[pid])
        
        # Look for unusual patterns
        suspicious = []
        
        # Group by destination
        dest_counts = defaultdict(int)
        for conn in connections:
            dest_counts[conn['dest']] += 1
        
        # Single destination with many connections = suspicious
        for dest, count in dest_counts.items():
            if count >= 10:  # Same destination 10+ times
                suspicious.append(dest)
        
        return suspicious
    
    def get_stats(self) -> Dict:
        """Get detection statistics"""
        return dict(self.stats)
    
    def reset_process(self, pid: int):
        """Reset tracking for a process (when it exits)"""
        if pid in self.connection_history:
            del self.connection_history[pid]
        if pid in self.port_access_history:
            del self.port_access_history[pid]
        if pid in self.bytes_sent:
            del self.bytes_sent[pid]
        if pid in self.bytes_received:
            del self.bytes_received[pid]

