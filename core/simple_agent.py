#!/usr/bin/env python3
"""
Simplified Security Agent - Minimal working version
This is a clean, simple implementation that actually works
"""
import os
import sys
import time
import signal
import threading
import logging
import traceback
import pickle
import json
from logging.handlers import RotatingFileHandler
from collections import defaultdict, deque, Counter
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

try:
    # Prefer explicit Central Time for log file naming so timestamps
    # match the demo / presentation timezone regardless of server TZ.
    from zoneinfo import ZoneInfo  # Python 3.9+
    _CENTRAL_TZ = ZoneInfo("America/Chicago")
except Exception:
    _CENTRAL_TZ = None

# Add core to path
_core_dir = os.path.dirname(os.path.abspath(__file__))
if _core_dir not in sys.path:
    sys.path.insert(0, _core_dir)

# Setup logging with file output
def setup_logging(log_dir=None):
    """Setup logging to both console and file with timestamped filename"""
    if log_dir is None:
        # Default: ~/.cache/security_agent/logs or ./logs
        home_log = Path.home() / '.cache' / 'security_agent' / 'logs'
        local_log = Path(__file__).parent.parent / 'logs'
        log_dir = local_log if local_log.exists() else home_log
    
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create timestamped log file: security_agent_YYYY-MM-DD_HH-MM-SS.log
    # Use US Central time (America/Chicago) for filenames so they align with the
    # expected demo timezone, even if the VM/system is running in UTC.
    if _CENTRAL_TZ is not None:
        timestamp = datetime.now(_CENTRAL_TZ).strftime('%Y-%m-%d_%H-%M-%S')
    else:
        # Fallback to local time if zoneinfo is unavailable
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    log_file = log_dir / f'security_agent_{timestamp}.log'
    
    # Also create a symlink to the latest log for backward compatibility
    latest_log = log_dir / 'security_agent.log'
    if latest_log.exists() and latest_log.is_symlink():
        latest_log.unlink()  # Remove old symlink
    try:
        latest_log.symlink_to(log_file.name)  # Create symlink to current log
    except (OSError, AttributeError):
        # Symlink creation failed (Windows or permission issue), just continue
        pass
    
    # Create formatters
    detailed_format = '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    console_format = '%(asctime)s - %(levelname)s - %(message)s'
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Remove existing handlers
    root_logger.handlers = []
    
    # File handler with rotation (10MB, keep 5 backups)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)  # More detailed in file
    file_handler.setFormatter(logging.Formatter(detailed_format))
    root_logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)  # Less verbose on console
    console_handler.setFormatter(logging.Formatter(console_format))
    root_logger.addHandler(console_handler)
    
    return str(log_file)

# Setup logging
log_file_path = setup_logging()
logger = logging.getLogger('security_agent.simple')
logger.info(f"📝 Logging to file: {log_file_path}")

# Imports
try:
    from core.collectors.collector_factory import get_collector
    from core.collectors.base import SyscallEvent
    from core.detection.risk_scorer import EnhancedRiskScorer
    from core.utils.validator import validate_system, print_validation_results
except ImportError:
    # Fallback for direct execution
    from collectors.collector_factory import get_collector
    from collectors.base import SyscallEvent
    from detection.risk_scorer import EnhancedRiskScorer
    from utils.validator import validate_system, print_validation_results

try:
    from enhanced_anomaly_detector import EnhancedAnomalyDetector
    ML_AVAILABLE = True
except ImportError:
    try:
        from core.enhanced_anomaly_detector import EnhancedAnomalyDetector
        ML_AVAILABLE = True
    except ImportError:
        ML_AVAILABLE = False
        EnhancedAnomalyDetector = None

# Connection pattern analyzer
try:
    from connection_pattern_analyzer import ConnectionPatternAnalyzer
    CONN_PATTERN_AVAILABLE = True
except ImportError:
    try:
        from core.connection_pattern_analyzer import ConnectionPatternAnalyzer
        CONN_PATTERN_AVAILABLE = True
    except ImportError:
        CONN_PATTERN_AVAILABLE = False
        ConnectionPatternAnalyzer = None

# Response handler for automated actions
try:
    from response_handler import ResponseHandler
    RESPONSE_HANDLER_AVAILABLE = True
except ImportError:
    try:
        from core.response_handler import ResponseHandler
        RESPONSE_HANDLER_AVAILABLE = True
    except ImportError:
        RESPONSE_HANDLER_AVAILABLE = False
        ResponseHandler = None

import psutil
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich import box


class SimpleSecurityAgent:
    """Simplified security agent - just the essentials"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.console = Console()
        self.running = False
        
        # Components
        self.collector = None
        self.risk_scorer = EnhancedRiskScorer(config)
        self.anomaly_detector = None
        
        # Connection pattern analyzer (for C2, port scanning, exfiltration)
        if CONN_PATTERN_AVAILABLE:
            self.connection_analyzer = ConnectionPatternAnalyzer(config)
            logger.info("✅ Connection pattern analyzer enabled")
        else:
            self.connection_analyzer = None
        
        # Response handler for automated actions (optional, disabled by default for safety)
        if RESPONSE_HANDLER_AVAILABLE:
            # Only enable if explicitly configured (safety first!)
            response_config = config.get('response', {})
            response_config['enable_responses'] = response_config.get('enable_responses', False)
            response_config['enable_kill'] = response_config.get('enable_kill', False)  # Very dangerous!
            response_config['enable_isolation'] = response_config.get('enable_isolation', False)
            # Set high thresholds for safety - only act on very high risk
            response_config['warn_threshold'] = response_config.get('warn_threshold', 70.0)
            response_config['freeze_threshold'] = response_config.get('freeze_threshold', 85.0)
            response_config['isolate_threshold'] = response_config.get('isolate_threshold', 90.0)
            response_config['kill_threshold'] = response_config.get('kill_threshold', 95.0)
            self.response_handler = ResponseHandler(response_config)
            if self.response_handler.enabled:
                logger.warning("⚠️  Automated response ENABLED - use with caution!")
            else:
                logger.info("ℹ️  Response handler available but disabled (safe mode)")
        else:
            self.response_handler = None
        
        # Process tracking (will be reset in __init__ after stats)
        # self.processes = {}  # Moved below to ensure reset
        self.processes_lock = threading.Lock()
        
        # Process name cache - persists even after process ends (TTL: 5 minutes)
        # This helps resolve names for short-lived processes
        self.process_name_cache = {}  # pid -> (name, timestamp)
        self.process_name_cache_ttl = 300  # 5 minutes
        
        # Rate limiting for alerts (prevent spam from same process)
        self.alert_cooldown = {}  # pid -> last_alert_time
        self.alert_cooldown_seconds = 120  # Don't alert same process more than once per 2 minutes (increased to reduce FPR)
        
        # Stats - now tracking current state, not cumulative
        # RESET on agent initialization to ensure clean state
        self.stats = {
            'total_processes': 0,  # Current active processes
            'high_risk': 0,  # Current high-risk processes
            'anomalies': 0,  # Current anomalous processes
            'total_syscalls': 0,  # Cumulative (useful as throughput metric)
            'c2_beacons': 0,  # Recent C2 detections (last 5 minutes)
            'port_scans': 0  # Recent port scans (last 5 minutes)
        }
        
        # Track recent detections with timestamps (for C2/Scans)
        # RESET on agent initialization to ensure clean state
        self.recent_c2_detections = deque(maxlen=1000)  # Store timestamps
        self.recent_scan_detections = deque(maxlen=1000)  # Store timestamps
        
        # Clear process tracking on initialization
        self.processes = {}
        self.process_timeout = 60  # Process considered inactive after 60 seconds
        
        # Cache info panel to prevent re-creation (reduces blinking)
        self._info_panel_cache = None
        
        # Store agent's own PID to exclude from detection (prevent self-detection false positives)
        self.agent_pid = os.getpid()
        logger.info(f"Agent PID: {self.agent_pid} (will be excluded from detection)")
        
        # Warm-up period: Suppress connection pattern detections during first few minutes
        # This prevents false positives from normal system startup activity (SSH, DNS, package checks, etc.)
        self.startup_time = time.time()
        self.warmup_period_seconds = self.config.get('warmup_period_seconds', 180)  # 3 minutes default
        logger.info(f"Warm-up period: {self.warmup_period_seconds}s (connection pattern detections suppressed during startup)")
        
        # Known system processes to exclude (optional, can be configured)
        self.excluded_pids = set([self.agent_pid])
        
        # Default system processes to exclude (known safe system daemons and utilities)
        # NOTE: python3/python NOT excluded - attack simulations need to be detected!
        default_excluded = ['fluent-bit', 'containerd', 'otelopscol', 'multipathd', 
                           'google_osconfig_agent', 'google_guest_agent', 'systemd', 'systemd-logind', 
                           'systemd-networkd', 'systemd-resolved', 'snapd', 'sudo',
                           'sshd', 'bash', 'sh', 'dash', 'zsh',
                           'systemd-journald', 'systemd-udevd', 'dbus-daemon', 'NetworkManager',
                           'dockerd', 'packagekitd', 'packagekit', 'gdm', 'gnome-shell',
                           'pulseaudio', 'avahi-daemon', 'cron', 'rsyslog',
                           'clear', 'ls', 'cat', 'grep', 'echo', 'which', 'whereis']  # Common harmless utilities
        
        # Merge config and defaults
        excluded_processes = self.config.get('excluded_processes', [])
        self.excluded_process_names = set(default_excluded + excluded_processes)
        
        if self.excluded_process_names:
            logger.info(f"Excluding system processes from detection: {sorted(self.excluded_process_names)}")
        
        # Initialize ML if available
        if ML_AVAILABLE:
            try:
                logger.info("Initializing ML anomaly detector...")
                self.anomaly_detector = EnhancedAnomalyDetector(config)
                logger.info(f"ML detector initialized. Model directory: {getattr(self.anomaly_detector, 'model_dir', 'default')}")
                
                # Try to load pre-trained models
                try:
                    logger.debug("Attempting to load pre-trained ML models...")
                    load_result = self.anomaly_detector._load_models()
                    if self.anomaly_detector.is_fitted:
                        models_loaded = [name for name, trained in self.anomaly_detector.models_trained.items() if trained]
                        logger.info(f"✅ Loaded pre-trained ML models: {', '.join(models_loaded) if models_loaded else 'all models'}")
                        logger.info(f"   Models available: IsolationForest={models_loaded.count('isolation_forest')>0}, "
                                  f"SVM={models_loaded.count('one_class_svm')>0}, "
                                  f"Scaler={hasattr(self.anomaly_detector, 'scaler') and self.anomaly_detector.scaler is not None}, "
                                  f"PCA={hasattr(self.anomaly_detector, 'pca') and self.anomaly_detector.pca is not None}")
                    else:
                        logger.warning("⚠️  ML models not fully loaded - some components missing")
                        logger.warning(f"   is_fitted={self.anomaly_detector.is_fitted}, "
                                     f"models_trained={self.anomaly_detector.models_trained}")
                except FileNotFoundError as e:
                    logger.info(f"ℹ️  No pre-trained models found at expected location: {e}")
                    logger.info("   Train models with: python3 scripts/train_with_dataset.py")
                except pickle.UnpicklingError as e:
                    logger.error(f"❌ Error loading ML models (corrupted file): {e}")
                    logger.error("   Models may be corrupted. Retrain with: python3 scripts/train_with_dataset.py")
                except Exception as e:
                    logger.error(f"❌ Error loading ML models: {type(e).__name__}: {e}")
                    logger.debug(f"   Full traceback: {traceback.format_exc()}")
                    logger.info("   Agent will continue without ML detection. Train models to enable ML features.")
            except ImportError as e:
                logger.warning(f"⚠️  ML detector import failed: {e}")
                logger.warning("   ML features will be disabled")
            except Exception as e:
                logger.error(f"❌ ML detector initialization failed: {type(e).__name__}: {e}")
                logger.debug(f"   Full traceback: {traceback.format_exc()}")
                logger.warning("   Agent will continue without ML detection")
    
    def start(self) -> bool:
        """Start the agent"""
        # RESET everything when starting (clean slate for new run)
        logger.info("🔄 Resetting agent state for new run...")
        self.stats = {
            'total_processes': 0,
            'high_risk': 0,
            'anomalies': 0,
            'total_syscalls': 0,
            'c2_beacons': 0,
            'port_scans': 0
        }
        self.recent_c2_detections.clear()
        self.recent_scan_detections.clear()
        self.processes.clear()  # Clear all processes
        self.process_name_cache.clear()  # Clear name cache
        self.alert_cooldown.clear()  # Clear alert cooldowns
        logger.info("✅ Agent state reset - starting fresh monitoring session")
        
        logger.info("="*60)
        logger.info("Starting Security Agent...")
        logger.info(f"Collector type: {self.config.get('collector', 'ebpf')}")
        logger.info(f"Risk threshold: {self.config.get('risk_threshold', 30.0)}")
        logger.info(f"ML detector available: {self.anomaly_detector is not None}")
        logger.info(f"Connection analyzer available: {self.connection_analyzer is not None}")
        
        # Validate system
        logger.debug("Validating system requirements...")
        is_valid, errors = validate_system(self.config)
        if not is_valid:
            logger.error("System validation failed:")
            for error in errors:
                logger.error(f"  - {error}")
            print_validation_results(False, errors)
            return False
        logger.info("✅ System validation passed")
        
        # Get collector (default to eBPF, fallback to auditd)
        collector_type = self.config.get('collector', 'ebpf')
        logger.info(f"Initializing collector: {collector_type}")
        self.collector = get_collector(self.config, preferred=collector_type)
        if not self.collector:
            logger.error("❌ No collector available - cannot start agent")
            return False
        logger.info(f"✅ Collector initialized: {self.collector.get_name()}")
        
        # Start collector
        logger.info("Starting event monitoring...")
        if not self.collector.start_monitoring(self._handle_event):
            logger.error("❌ Failed to start collector - cannot start agent")
            return False
        
        self.running = True
        logger.info(f"✅ Agent started successfully with {self.collector.get_name()}")
        
        # Health check: Wait a few seconds and verify events are being captured
        logger.info("Performing health check (waiting 5 seconds for events)...")
        initial_syscalls = self.stats['total_syscalls']
        time.sleep(5)
        events_captured = self.stats['total_syscalls'] - initial_syscalls
        
        if events_captured > 0:
            logger.info(f"✅ Health check passed: Captured {events_captured} syscalls in 5 seconds")
            logger.info(f"   Capture rate: ~{events_captured/5:.0f} syscalls/second")
        else:
            logger.warning("⚠️  Health check warning: No events captured in 5 seconds")
            logger.warning("   This may indicate:")
            logger.warning("   - eBPF not capturing events (check kernel support)")
            logger.warning("   - No system activity (normal if system is idle)")
            logger.warning("   - Collector issue (check logs for errors)")
            logger.warning("   Agent will continue, but monitor for events...")
        
        logger.info("="*60)
        return True
    
    def _resolve_process_name(self, pid: int, event_comm: Optional[str] = None, event_exe: Optional[str] = None) -> str:
        """
        Resolve process name with aggressive caching.
        Tries multiple methods and caches result even if process ends.
        """
        current_time = time.time()
        
        # Check cache first (even for ended processes)
        # But if cached name is pid_XXXXX, try to resolve again (process might still be alive)
        if pid in self.process_name_cache:
            cached_name, cache_time = self.process_name_cache[pid]
            if current_time - cache_time < self.process_name_cache_ttl:
                if cached_name and not cached_name.startswith('pid_') and len(cached_name) > 0:
                    return cached_name
                # If cached name is pid_XXXXX, don't return it - try to resolve again
        
        # Try event.exe first (from eBPF, most reliable - executable path)
        process_name = None
        if event_exe and len(event_exe) > 0:
            # Extract basename from exe path
            process_name = os.path.basename(event_exe)
            if process_name and not process_name.startswith('pid_') and len(process_name) > 0:
                # Cache immediately and return
                self.process_name_cache[pid] = (process_name, current_time)
                return process_name
        
        # Try event.comm FIRST (from eBPF, available immediately at syscall time)
        # This is the most reliable source - captured directly in kernel
        if not process_name or process_name.startswith('pid_') or len(process_name) == 0:
            if event_comm and len(event_comm) > 0 and not event_comm.startswith('pid_'):
                # Clean up comm (remove null bytes, whitespace)
                cleaned_comm = event_comm.strip().replace('\x00', '')
                if cleaned_comm and len(cleaned_comm) > 0:
                    process_name = cleaned_comm
                    # Cache immediately - this is from eBPF, most reliable
                    self.process_name_cache[pid] = (process_name, current_time)
                    return process_name
        
        # Try psutil methods (multiple attempts)
        if not process_name or process_name.startswith('pid_') or len(process_name) == 0:
            try:
                p = psutil.Process(pid)
                # Try name() first (fastest)
                try:
                    name = p.name()
                    if name and not name.startswith('pid_') and len(name) > 0:
                        process_name = name
                except (psutil.NoSuchProcess, psutil.AccessDenied, OSError):
                    pass
                
                # If still empty, try exe()
                if not process_name or process_name.startswith('pid_') or len(process_name) == 0:
                    try:
                        exe = p.exe()
                        if exe:
                            process_name = os.path.basename(exe)
                    except (psutil.NoSuchProcess, psutil.AccessDenied, OSError):
                        pass
                
                # If still empty, try cmdline()
                if not process_name or process_name.startswith('pid_') or len(process_name) == 0:
                    try:
                        cmdline = p.cmdline()
                        if cmdline and len(cmdline) > 0 and cmdline[0]:
                            process_name = os.path.basename(cmdline[0])
                    except (psutil.NoSuchProcess, psutil.AccessDenied, OSError):
                        pass
            except (psutil.NoSuchProcess, psutil.AccessDenied, OSError):
                # Process already ended or no access
                pass
        
        # Fallback to event.comm or pid_ format
        if not process_name or process_name.startswith('pid_') or len(process_name) == 0:
            if event_comm and len(event_comm) > 0:
                process_name = event_comm
            else:
                process_name = f'pid_{pid}'
        
        # Cache the result (even if it's pid_XXXXX, cache it to avoid repeated lookups)
        self.process_name_cache[pid] = (process_name, current_time)
        
        # Clean old cache entries (keep cache size reasonable)
        if len(self.process_name_cache) > 10000:
            # Remove entries older than TTL
            expired_pids = [pid for pid, (_, cache_time) in self.process_name_cache.items()
                          if current_time - cache_time > self.process_name_cache_ttl]
            for expired_pid in expired_pids:
                self.process_name_cache.pop(expired_pid, None)
        
        return process_name
    
    def stop(self):
        """Stop the agent"""
        logger.info("Stopping agent...")
        self.running = False
        if self.collector:
            logger.debug("Stopping collector...")
            self.collector.stop_monitoring()
            logger.debug("Collector stopped")
        
        # Log final statistics (calculate current stats, not cumulative)
        current_time = time.time()
        current_processes = sum(1 for p in self.processes.values() 
                               if current_time - p['last_update'] < self.process_timeout)
        current_anomalies = sum(1 for p in self.processes.values() 
                               if current_time - p['last_update'] < self.process_timeout 
                               and p.get('anomaly_score', 0) >= 60.0)
        recent_c2 = self._count_recent_detections(self.recent_c2_detections)
        recent_scans = self._count_recent_detections(self.recent_scan_detections)
        
        logger.info("="*60)
        logger.info("Agent stopped - Final Statistics:")
        logger.info(f"  Current active processes: {current_processes}")
        logger.info(f"  Total syscalls processed: {self.stats['total_syscalls']}")
        logger.info(f"  Current high risk processes: {self.stats['high_risk']}")
        logger.info(f"  Current anomalous processes: {current_anomalies}")
        logger.info(f"  Recent C2 beacons (last 5min): {recent_c2}")
        logger.info(f"  Recent port scans (last 5min): {recent_scans}")
        logger.info("="*60)
    
    def _handle_event(self, event: SyscallEvent):
        """Handle syscall event"""
        if not self.running:
            return
        
        try:
            # Skip detection for agent's own PID (prevent self-detection false positives)
            if event.pid == self.agent_pid or event.pid in self.excluded_pids:
                return
            
            # PRIORITY: Use event.comm FIRST (from eBPF, available immediately, most reliable)
            # eBPF's bpf_get_current_comm() captures the process name at syscall time
            process_name = None
            if hasattr(event, 'comm') and event.comm and len(event.comm) > 0 and not event.comm.startswith('pid_'):
                process_name = event.comm.strip()
                # Cache it immediately since it's from eBPF (most reliable source)
                self.process_name_cache[event.pid] = (process_name, time.time())
            
            # If comm not available or invalid, use resolver
            if not process_name or process_name.startswith('pid_') or len(process_name) == 0:
                process_name = self._resolve_process_name(event.pid, event.comm, event.exe)
            
            # Skip detection for known system processes (reduce false positives)
            # IMPROVEMENT: Don't exclude sudo if it's wrapping python3 (for attack detection)
            # Check if this is a sudo-wrapped python3 process
            is_sudo_python = (process_name.lower() == 'sudo' and 
                            hasattr(event, 'exe') and event.exe and 
                            'python' in event.exe.lower())
            
            # Check exact match, case-insensitive match, and partial match (for paths like /usr/sbin/sshd)
            process_name_lower = process_name.lower()
            excluded_lower = [p.lower() for p in self.excluded_process_names]
            
            # Check if process name matches any excluded process (exact or partial)
            # BUT: Don't exclude sudo wrapping python3 (needed for attack detection)
            is_excluded = (
                not is_sudo_python and (  # Don't exclude sudo wrapping python3
                    process_name in self.excluded_process_names or
                    process_name_lower in excluded_lower or
                    any(excluded in process_name_lower for excluded in excluded_lower) or
                    any(process_name_lower in excluded for excluded in excluded_lower)
                )
            )
            
            if is_excluded:
                logger.debug(f"⏭️  Skipping excluded system process: PID={event.pid} Name={process_name}")
                return
            
            # If sudo wrapping python3, update process name to python3 for better tracking
            if is_sudo_python:
                process_name = 'python3'
                logger.debug(f"🔍 Detected sudo-wrapped python3: PID={event.pid} -> treating as python3")
            
            # DEBUG: Log first few events AND all python3 events to confirm flow
            event_comm = getattr(event, 'comm', 'N/A')
            is_python = 'python' in str(event_comm).lower() or 'python' in str(process_name).lower()
            
            # Log python3 events and network syscalls for debugging
            syscall_normalized = event.syscall.strip().lower() if event.syscall else ''
            is_network_syscall = syscall_normalized in ['socket', 'connect', 'sendto', 'sendmsg']
            
            if self.stats['total_syscalls'] < 5 or is_python or is_network_syscall:
                logger.info(f"🔍 EVENT RECEIVED: PID={event.pid} Syscall={event.syscall} Comm={event_comm} Process={process_name}")
                logger.info(f"   Is excluded: {is_excluded} | Is python: {is_python} | Is network: {is_network_syscall}")
                logger.debug(f"   Event details: {vars(event) if hasattr(event, '__dict__') else 'N/A'}")
            
            pid = event.pid
            syscall = event.syscall
            
            with self.processes_lock:
                # CRITICAL: Create process entry IMMEDIATELY before any checks
                # This ensures even short-lived processes are tracked
                if pid not in self.processes:
                    # Log when we're adding a new process (especially python3 or network syscalls)
                    if is_python or is_network_syscall:
                        logger.info(f"➕ Adding new process: PID={pid} Name={process_name} Syscall={syscall} (python={is_python}, network={is_network_syscall})")
                    # CRITICAL: Use event.comm FIRST (from eBPF, captured at syscall time, most reliable)
                    # This is available immediately and doesn't require process to still exist
                    process_name = None
                    if hasattr(event, 'comm') and event.comm and len(event.comm) > 0:
                        cleaned_comm = event.comm.strip().replace('\x00', '')
                        if cleaned_comm and not cleaned_comm.startswith('pid_') and len(cleaned_comm) > 0:
                            process_name = cleaned_comm
                            # Cache immediately - this is from eBPF kernel, most reliable
                            self.process_name_cache[pid] = (process_name, time.time())
                    
                    # If comm not available, try /proc filesystem (fastest fallback)
                    if not process_name or process_name.startswith('pid_') or len(process_name) == 0:
                        try:
                            # Read /proc/PID/comm (fastest method, works for very short processes)
                            comm_path = f"/proc/{pid}/comm"
                            if os.path.exists(comm_path):
                                with open(comm_path, 'r') as f:
                                    proc_comm = f.read().strip()
                                    if proc_comm and not proc_comm.startswith('pid_') and len(proc_comm) > 0:
                                        process_name = proc_comm
                                        self.process_name_cache[pid] = (process_name, time.time())
                        except (OSError, IOError, PermissionError):
                            pass
                    
                    # If still empty, try /proc/PID/cmdline (also fast)
                    if not process_name or process_name.startswith('pid_') or len(process_name) == 0:
                        try:
                            cmdline_path = f"/proc/{pid}/cmdline"
                            if os.path.exists(cmdline_path):
                                with open(cmdline_path, 'r') as f:
                                    cmdline = f.read().strip('\x00')
                                    if cmdline:
                                        # cmdline is null-separated, get first part
                                        first_arg = cmdline.split('\x00')[0] if '\x00' in cmdline else cmdline
                                        if first_arg:
                                            process_name = os.path.basename(first_arg)
                                            self.process_name_cache[pid] = (process_name, time.time())
                        except (OSError, IOError, PermissionError):
                            pass
                    
                    # Fallback to psutil if /proc didn't work
                    if not process_name or process_name.startswith('pid_') or len(process_name) == 0:
                        try:
                            p = psutil.Process(pid)
                            # Try name() first (fastest)
                            try:
                                process_name = p.name()
                                if process_name and not process_name.startswith('pid_'):
                                    self.process_name_cache[pid] = (process_name, time.time())
                            except (psutil.NoSuchProcess, psutil.AccessDenied, OSError):
                                pass
                            
                            # If still empty, try exe()
                            if not process_name or process_name.startswith('pid_') or len(process_name) == 0:
                                try:
                                    exe = p.exe()
                                    if exe:
                                        process_name = os.path.basename(exe)
                                        self.process_name_cache[pid] = (process_name, time.time())
                                except (psutil.NoSuchProcess, psutil.AccessDenied, OSError):
                                    pass
                        except (psutil.NoSuchProcess, psutil.AccessDenied, OSError):
                            # Process already ended, use cached resolver
                            process_name = self._resolve_process_name(pid, getattr(event, 'comm', None), getattr(event, 'exe', None))
                    
                    # Final fallback
                    if not process_name or process_name.startswith('pid_') or len(process_name) == 0:
                        process_name = self._resolve_process_name(pid, event.comm, event.exe)
                    
                    # Ensure we cache the final result
                    if process_name:
                        self.process_name_cache[pid] = (process_name, time.time())
                    
                    # CRITICAL FIX: Create process entry FIRST, then check exclusion
                    # This ensures we capture syscalls even from short-lived processes
                    # We'll remove it later if excluded, but at least we'll have the syscalls
                    self.processes[pid] = {
                        'name': process_name,
                        'syscalls': deque(maxlen=100),  # Last 100 for analysis
                        'total_syscalls': 0,  # Actual total count
                        'risk_score': 0.0,
                        'anomaly_score': 0.0,
                        'last_update': time.time()
                    }
                    
                    # Now check exclusion - if excluded, we'll remove it but syscalls are already captured
                    process_name_lower = process_name.lower()
                    excluded_lower = [p.lower() for p in self.excluded_process_names]
                    is_excluded_check = (
                        process_name in self.excluded_process_names or
                        process_name_lower in excluded_lower or
                        any(excluded in process_name_lower for excluded in excluded_lower)
                    )
                    
                    # If excluded, remove from processes dict but log it
                    if is_excluded_check:
                        logger.debug(f"⏭️  Process is excluded but was tracked: PID={pid} Name={process_name}")
                        # Don't return - continue to process the syscall so we at least log it
                        # But mark it as excluded for future checks
                        self.processes[pid]['_excluded'] = True
                else:
                    # Update process name if we have a better one (use cached resolver)
                    current_name = self.processes[pid]['name']
                    if not current_name or current_name.startswith('pid_') or len(current_name) == 0:
                        # Re-resolve using cache (will use cache if available, otherwise try fresh)
                        better_name = self._resolve_process_name(pid, event.comm, event.exe)
                        if better_name and not better_name.startswith('pid_') and len(better_name) > 0:
                            self.processes[pid]['name'] = better_name
                    
                    # Check if process should be excluded (name might have been updated)
                    proc_name = self.processes[pid]['name']
                    if proc_name and not proc_name.startswith('pid_') and len(proc_name) > 0:
                        proc_name_lower = proc_name.lower()
                        excluded_lower = [p.lower() for p in self.excluded_process_names]
                        is_excluded = (
                            proc_name in self.excluded_process_names or
                            proc_name_lower in excluded_lower or
                            any(excluded in proc_name_lower for excluded in excluded_lower)
                        )
                        if is_excluded:
                            # Remove from tracking
                            del self.processes[pid]
                            logger.debug(f"⏭️  Removed excluded process from tracking: PID={pid} Name={proc_name}")
                            return
                
                proc = self.processes[pid]
                proc['syscalls'].append(syscall)
                proc['total_syscalls'] += 1  # Increment actual total count
                proc['last_update'] = time.time()
                self.stats['total_syscalls'] += 1
                
                syscall_list = list(proc['syscalls'])
                
                # Initialize process_info (needed for risk scoring)
                process_info = {}
                try:
                    p = psutil.Process(pid)
                    process_info = {
                        'cpu_percent': p.cpu_percent(interval=0.1) if p.is_running() else 0.0,
                        'memory_percent': p.memory_percent() if p.is_running() else 0.0,
                        'num_threads': p.num_threads() if p.is_running() else 0
                    }
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    process_info = {}  # Use empty dict if process not available
                
                # Calculate anomaly score FIRST (needed for risk score)
                # Preserve previous anomaly score if ML fails temporarily
                previous_anomaly_score = proc.get('anomaly_score', 0.0)
                anomaly_score = previous_anomaly_score  # Default to previous score
                anomaly_result = None
                
                if self.anomaly_detector:
                    # Try to load models if not fitted (only log once per process)
                    if not self.anomaly_detector.is_fitted:
                        if pid not in getattr(self, '_model_load_attempted', set()):
                            if not hasattr(self, '_model_load_attempted'):
                                self._model_load_attempted = set()
                            self._model_load_attempted.add(pid)
                            
                            try:
                                logger.debug(f"Attempting to load ML models for PID {pid}...")
                                self.anomaly_detector._load_models()
                                if self.anomaly_detector.is_fitted:
                                    logger.info(f"✅ ML models loaded successfully for PID {pid}")
                                else:
                                    logger.warning(f"⚠️  ML models partially loaded for PID {pid} - some components missing")
                            except FileNotFoundError as e:
                                logger.debug(f"ML models not found for PID {pid}: {e}")
                            except pickle.UnpicklingError as e:
                                logger.error(f"❌ Corrupted ML model file for PID {pid}: {e}")
                            except Exception as e:
                                logger.warning(f"⚠️  Failed to load ML models for PID {pid}: {type(e).__name__}: {e}")
                                logger.debug(f"   Traceback: {traceback.format_exc()}")
                    
                    if self.anomaly_detector.is_fitted:
                        try:
                            # HONEST FIX: Require minimum syscalls before ML detection to reduce false positives
                            # Short-lived processes with few syscalls often trigger false positives
                            # Increased to 15 to further reduce false positives from very short processes
                            min_syscalls_for_ml = 15  # Only run ML on processes with 15+ syscalls
                            anomaly_result = None
                            
                            if len(syscall_list) < min_syscalls_for_ml:
                                # Too few syscalls - skip ML detection to avoid false positives
                                anomaly_score = 0.0
                                proc['anomaly_score'] = anomaly_score
                                proc['is_anomaly'] = False  # Explicitly set to False when skipping ML
                            else:
                                # CORRECT function signature: (syscalls, process_info, pid)
                                logger.debug(f"Running ML detection for PID {pid} (syscalls={len(syscall_list)})")
                                anomaly_result = self.anomaly_detector.detect_anomaly_ensemble(
                                    syscall_list, process_info, pid
                                )
                                anomaly_score = abs(anomaly_result.anomaly_score)  # Use absolute value
                                proc['anomaly_score'] = anomaly_score
                                proc['is_anomaly'] = anomaly_result.is_anomaly  # Store is_anomaly flag
                                proc['anomaly_explanation'] = anomaly_result.explanation  # Store explanation
                                proc['anomaly_confidence'] = anomaly_result.confidence  # Store confidence
                                
                                # Log ML result for first few processes or when anomaly detected
                                if len(syscall_list) == 20:  # First time we have 20 syscalls
                                    logger.info(f"🤖 ML RESULT: PID={pid} Process={proc['name']} "
                                              f"Score={anomaly_score:.1f} IsAnomaly={anomaly_result.is_anomaly} "
                                              f"Confidence={anomaly_result.confidence:.2f}")
                            
                            # IMMEDIATELY log anomaly if detected (outside the len==20 check so it always runs)
                            # Suppress during warm-up period to avoid false positives from startup
                            time_since_startup = time.time() - self.startup_time
                            if anomaly_result and anomaly_result.is_anomaly and anomaly_score >= 60.0:
                                current_time = time.time()
                                last_alert = self.alert_cooldown.get(pid, 0)
                                anomaly_cooldown = 5.0  # 5 seconds between anomaly logs
                                if current_time - last_alert >= anomaly_cooldown:
                                    # Only log if warm-up period has ended
                                    if time_since_startup >= self.warmup_period_seconds:
                                        comm = proc.get('name', 'unknown')
                                        # Get current risk score if available, otherwise use 0
                                        current_risk = proc.get('risk_score', 0.0)
                                        logger.warning(f"🤖 ANOMALY DETECTED: PID={pid} Process={comm} AnomalyScore={anomaly_score:.1f} Risk={current_risk:.1f}")
                                        logger.warning(f"   ┌─ What's Anomalous:")
                                        logger.warning(f"   │  {anomaly_result.explanation}")
                                        logger.warning(f"   │  Confidence: {anomaly_result.confidence:.2f}")
                                        self.alert_cooldown[pid] = current_time
                                    else:
                                        logger.debug(f"⏳ Suppressing anomaly detection during warm-up (PID={pid}, Score={anomaly_score:.1f})")
                            
                            if anomaly_result and anomaly_result.is_anomaly:
                                # Don't increment cumulative - will calculate current count dynamically
                                logger.debug(f"Anomaly detected: PID={pid} Score={anomaly_score:.1f} "
                                           f"Explanation={anomaly_result.explanation}")
                                # Track anomaly detection for stats (only count after warm-up)
                                if time_since_startup >= self.warmup_period_seconds:
                                self.stats['anomalies'] = sum(1 for p in self.processes.values() 
                                                             if p.get('anomaly_score', 0) >= 70.0)
                                else:
                                    # During warm-up, set anomalies to 0
                                    self.stats['anomalies'] = 0
                        except ValueError as e:
                            logger.warning(f"⚠️  ML detection ValueError for PID {pid}: {e}")
                            logger.debug(f"   This may indicate insufficient features or data. Traceback: {traceback.format_exc()}")
                            # Keep previous score instead of resetting to 0
                            anomaly_score = previous_anomaly_score
                            proc['anomaly_score'] = anomaly_score
                        except AttributeError as e:
                            logger.error(f"❌ ML detection AttributeError for PID {pid}: {e}")
                            logger.error(f"   ML model may be corrupted. Traceback: {traceback.format_exc()}")
                            anomaly_score = previous_anomaly_score
                            proc['anomaly_score'] = anomaly_score
                        except Exception as e:
                            logger.error(f"❌ ML detection failed for PID {pid}: {type(e).__name__}: {e}")
                            logger.error(f"   Traceback: {traceback.format_exc()}")
                            # Keep previous score instead of resetting to 0
                            anomaly_score = previous_anomaly_score
                            proc['anomaly_score'] = anomaly_score
                    else:
                        # ML not trained yet - keep previous score or set to 0.00
                        if previous_anomaly_score == 0.0:
                            logger.debug(f"ML not fitted for PID {pid} - using default score 0.0")
                        anomaly_score = previous_anomaly_score if previous_anomaly_score > 0 else 0.0
                        proc['anomaly_score'] = anomaly_score
                else:
                    # No ML detector available
                    anomaly_score = previous_anomaly_score if previous_anomaly_score > 0 else 0.0
                    proc['anomaly_score'] = anomaly_score
                    if pid not in getattr(self, '_ml_unavailable_logged', set()):
                        if not hasattr(self, '_ml_unavailable_logged'):
                            self._ml_unavailable_logged = set()
                        self._ml_unavailable_logged.add(pid)
                        logger.debug(f"ML detector not available for PID {pid}")
                
                # Check for network connection patterns (C2, port scanning, exfiltration)
                connection_risk_bonus = 0.0
                # INFO: Log all network syscalls to verify they're being captured
                # Normalize syscall name (strip whitespace, lowercase for comparison)
                syscall_normalized = syscall.strip().lower() if syscall else ''
                network_syscalls = ['socket', 'connect', 'sendto', 'sendmsg']
                is_network_syscall = syscall_normalized in network_syscalls
                
                if is_network_syscall:
                    logger.info(f"🔍 NETWORK SYSCALL DETECTED: '{syscall}' (normalized: '{syscall_normalized}') for PID {pid} Process={proc.get('name', 'unknown')} (total_syscalls={proc.get('total_syscalls', 0)})")
                
                if self.connection_analyzer and is_network_syscall:
                    try:
                        # Extract connection info from event
                        dest_ip = '0.0.0.0'
                        dest_port = 0
                        event_info = None
                        
                        # Try to get from event.event_info if available
                        if hasattr(event, 'event_info') and event.event_info:
                            event_info = event.event_info
                            dest_ip = event_info.get('dest_ip', '0.0.0.0')
                            dest_port = event_info.get('dest_port', 0)
                            logger.debug(f"Connection event for PID {pid}: syscall={syscall} dest_ip={dest_ip} dest_port={dest_port}")
                        else:
                            logger.debug(f"Connection event for PID {pid}: syscall={syscall} (no event_info available)")
                        
                        # For socket/connect syscalls, try to extract real port from syscall arguments
                        # If not available, use simulated port for pattern detection
                        if dest_port == 0 and syscall_normalized in ['socket', 'connect']:
                            # Try to get real port from event_info if available
                            if event_info and isinstance(event_info, dict):
                                # Check for common port fields in event_info
                                real_port = event_info.get('port') or event_info.get('dest_port') or event_info.get('dport')
                                if real_port:
                                    try:
                                        dest_port = int(real_port)
                                        logger.info(f"Using real port from event_info for PID {pid}: {dest_port}")
                                    except (ValueError, TypeError):
                                        pass
                            
                            # CRITICAL FIX: Always generate simulated port if real port not available
                            # This ensures port scanning detection works even without real port extraction
                            if dest_port == 0:
                                import hashlib
                                
                                # FIXED: Port simulation strategy for C2 beaconing detection
                                # For C2 beaconing: Need SAME port for multiple connections (regular intervals)
                                # For port scanning: Need DIFFERENT ports for multiple connections (5+ unique ports)
                                
                                # Strategy: Check connection history to determine pattern
                                # If connections are spaced out (potential C2), use same port
                                # If connections are rapid (potential port scan), vary ports
                                connection_count = proc.get('connection_count', 0)
                                proc['connection_count'] = connection_count + 1
                                
                                # Check if this might be C2 beaconing (spaced out connections)
                                # If we have previous connections and they're spaced out, use same port
                                if self.connection_analyzer and pid in self.connection_analyzer.connection_history:
                                    prev_connections = list(self.connection_analyzer.connection_history[pid])
                                    if len(prev_connections) >= 2:
                                        # Check if intervals are regular (C2 pattern)
                                        last_interval = time.time() - prev_connections[-1]['time']
                                        if last_interval >= 2.0:  # Spaced out = potential C2
                                            # Use same port as last connection for C2 detection
                                            dest_port = prev_connections[-1]['port']
                                            logger.debug(f"🔍 Using same port for C2 pattern: {dest_port} (interval: {last_interval:.1f}s)")
                                        else:
                                            # Rapid connections = port scanning, vary ports
                                            port_seed = f"{pid}_{dest_ip}_{connection_count}"
                                            port_hash = int(hashlib.md5(port_seed.encode()).hexdigest()[:8], 16)
                                            dest_port = 8000 + (port_hash % 200)
                                            logger.debug(f"🔍 Varying port for scan pattern: {dest_port} (connection #{connection_count})")
                                    else:
                                        # First few connections - use consistent port (allows C2 detection)
                                        port_seed = f"{pid}_{dest_ip}"  # Same seed = same port
                                        port_hash = int(hashlib.md5(port_seed.encode()).hexdigest()[:8], 16)
                                        dest_port = 8000 + (port_hash % 200)
                                        logger.debug(f"🔍 Generated consistent port for PID {pid}: {dest_port}")
                                else:
                                    # No history yet - use consistent port (allows C2 detection)
                                    port_seed = f"{pid}_{dest_ip}"  # Same seed = same port
                                    port_hash = int(hashlib.md5(port_seed.encode()).hexdigest()[:8], 16)
                                    dest_port = 8000 + (port_hash % 200)
                                    logger.debug(f"🔍 Generated initial port for PID {pid}: {dest_port}")
                        
                        # CRITICAL: Only analyze if we have a valid port (not 0)
                        if dest_port > 0:
                            # Analyze connection pattern
                            # Pass process name to enable tracking across PID changes (for C2 beaconing)
                            process_name = proc.get('name', 'unknown')
                            logger.info(f"🔍 Analyzing connection pattern for PID {pid} ({process_name}): IP={dest_ip} Port={dest_port} Syscall={syscall}")
                            conn_result = self.connection_analyzer.analyze_connection(
                                pid=pid,
                                dest_ip=dest_ip,
                                dest_port=dest_port,
                                timestamp=time.time(),
                                process_name=process_name  # Enable process name tracking for C2
                            )
                            
                            # Only log result if it's a detection (after warm-up check)
                            if conn_result:
                                logger.debug(f"🔍 Connection analysis result for PID {pid}: {conn_result}")
                        else:
                            logger.warning(f"⚠️  Skipping connection analysis for PID {pid}: dest_port is 0 (no port available)")
                            conn_result = None
                        
                        if conn_result:
                            # Check if we're still in warm-up period (suppress false positives from startup)
                            time_since_startup = time.time() - self.startup_time
                            if time_since_startup < self.warmup_period_seconds:
                                remaining_warmup = self.warmup_period_seconds - time_since_startup
                                # Only log once when warm-up period ends (avoid spam)
                                if not hasattr(self, '_warmup_logged') or not self._warmup_logged:
                                    logger.info(f"⏳ Warm-up period active: Suppressing connection pattern detections for {(remaining_warmup):.0f}s (prevents false positives from startup)")
                                    self._warmup_logged = True
                                conn_result = None  # Ignore detection during warm-up
                            elif time_since_startup >= self.warmup_period_seconds and not hasattr(self, '_warmup_ended_logged'):
                                logger.info(f"✅ Warm-up period ended - connection pattern detections are now active")
                                self._warmup_ended_logged = True
                        
                        if conn_result:
                            connection_risk_bonus = 30.0  # Boost risk for connection patterns
                            pattern_type = conn_result.get('type', 'UNKNOWN')
                            explanation = conn_result.get('explanation', 'No explanation')
                            
                            logger.warning(f"🌐 CONNECTION PATTERN DETECTED: {pattern_type} PID={pid} Process={proc['name']}")
                            logger.warning(f"   Details: {explanation}")
                            logger.warning(f"   Destination: {dest_ip}:{dest_port} (NOTE: Port may be simulated)")
                            logger.warning(f"   Risk bonus added: +{connection_risk_bonus:.1f}")
                            
                            # Update stats
                            if pattern_type == 'C2_BEACONING':
                                # Track with timestamp for recent count
                                detection_time = time.time()
                                self.recent_c2_detections.append(detection_time)
                                count = self._count_recent_detections(self.recent_c2_detections)
                                self.stats['c2_beacons'] = count
                                logger.warning(f"   C2 beaconing detected (recent count: {count}, total detections in history: {len(self.recent_c2_detections)})")
                                # Force immediate state file update so dashboard shows attack quickly
                                try:
                                    self._write_state_file()
                                    logger.info(f"✅ State file updated immediately with C2 beacon count: {count}")
                                except Exception as e:
                                    logger.error(f"❌ Could not force state file write: {e}")
                            elif pattern_type == 'PORT_SCANNING':
                                # Track with timestamp for recent count
                                detection_time = time.time()
                                self.recent_scan_detections.append(detection_time)
                                count = self._count_recent_detections(self.recent_scan_detections)
                                self.stats['port_scans'] = count
                                logger.warning(f"   Port scan detected (recent count: {count}, total detections in history: {len(self.recent_scan_detections)})")
                                # Force immediate state file update so dashboard shows attack quickly
                                try:
                                    self._write_state_file()
                                    logger.info(f"✅ State file updated immediately with port scan count: {count}")
                                except Exception as e:
                                    logger.error(f"❌ Could not force state file write: {e}")
                    except AttributeError as e:
                        logger.debug(f"Connection pattern analysis AttributeError for PID {pid}: {e}")
                        logger.debug(f"   Traceback: {traceback.format_exc()}")
                    except KeyError as e:
                        logger.debug(f"Connection pattern analysis KeyError for PID {pid}: {e}")
                        logger.debug(f"   Missing key in connection result. Traceback: {traceback.format_exc()}")
                    except Exception as e:
                        # Don't fail on connection analysis errors
                        logger.warning(f"⚠️  Connection pattern analysis error for PID {pid}: {type(e).__name__}: {e}")
                        logger.debug(f"   Traceback: {traceback.format_exc()}")
                
                # Calculate risk score WITH anomaly score AND connection pattern bonus
                base_risk_score = self.risk_scorer.update_risk_score(
                    pid, syscall_list, process_info, anomaly_score
                )
                risk_score = base_risk_score + connection_risk_bonus
                proc['risk_score'] = risk_score
                
                # Log SCORE UPDATE with reduced frequency to prevent log spam
                # Only log if process has meaningful activity (at least 20 syscalls)
                # AND either: (1) reached 50/100/150... syscalls OR (2) 15 seconds passed with significant activity
                current_time = time.time()
                last_score_update = proc.get('_last_score_update_time', 0)
                syscall_count = len(syscall_list)
                
                should_log_score = False
                if syscall_count >= 20:  # Minimum threshold to prevent spam
                    time_since_last = current_time - last_score_update
                    # Only log if 15 seconds have passed (enforce minimum interval)
                    if time_since_last >= 15.0:
                        # Log every 15 seconds for processes with meaningful activity
                        # (Milestone logging at 50/100/150 is nice but not required)
                        should_log_score = True
                
                if should_log_score:
                    # Get process name using cached resolver (will use cache if available)
                    comm = proc.get('name', 'unknown')
                    if comm.startswith('pid_') or not comm or comm == 'unknown':
                        # Try to get better name from cache or fresh lookup
                        # Try to get better name - we don't have event here, so try with None
                        # But first check if we have exe in process info
                        better_name = self._resolve_process_name(pid, None, None)
                        if better_name and not better_name.startswith('pid_') and len(better_name) > 0:
                                comm = better_name
                                proc['name'] = better_name  # Update stored name
                    
                    # Always log SCORE UPDATE for dashboard tracking (TotalSyscalls)
                    # But use different log levels based on significance
                    log_level = logger.info
                    if risk_score > 30 or anomaly_score > 40:
                        log_level = logger.warning  # More visible for high-risk
                    
                    log_level(f"📊 SCORE UPDATE: PID={pid} Process={comm} Risk={risk_score:.1f} Anomaly={anomaly_score:.1f} "
                              f"Syscalls={len(syscall_list)} TotalSyscalls={proc.get('total_syscalls', 0)} "
                              f"ConnectionBonus={connection_risk_bonus:.1f}")
                    logger.debug(f"   Process info: CPU={process_info.get('cpu_percent', 0):.1f}% "
                               f"Memory={process_info.get('memory_percent', 0):.1f}% "
                               f"Threads={process_info.get('num_threads', 0)}")
                    # Store last logged values
                    proc['_last_logged_risk'] = risk_score
                    proc['_last_logged_anomaly'] = anomaly_score
                    proc['_last_score_update_time'] = current_time
                
                # Update high risk count and LOG detections (with rate limiting)
                threshold = self.config.get('risk_threshold', 30.0)
                if risk_score >= threshold:
                    # Check warm-up period
                    time_since_startup = time.time() - self.startup_time
                    
                    # Only count high-risk processes after warm-up period
                    if time_since_startup >= self.warmup_period_seconds:
                    self.stats['high_risk'] = sum(1 for p in self.processes.values() 
                                                 if p['risk_score'] >= threshold)
                    else:
                        # During warm-up, set high_risk to 0
                        self.stats['high_risk'] = 0
                    
                    # Rate limiting: only log if enough time has passed since last alert
                    current_time = time.time()
                    last_alert = self.alert_cooldown.get(pid, 0)
                    if current_time - last_alert >= self.alert_cooldown_seconds:
                        # Only log high-risk detections after warm-up period
                        if time_since_startup >= self.warmup_period_seconds:
                        # LOG HIGH-RISK DETECTION with full details
                        comm = proc.get('name', 'unknown')
                        # Try to get better process name if current one is pid_XXXXX
                        if comm.startswith('pid_'):
                            try:
                                p = psutil.Process(pid)
                                better_name = p.name()
                                if better_name and not better_name.startswith('pid_'):
                                    comm = better_name
                                    proc['name'] = better_name  # Update stored name
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                pass
                        logger.warning(f"🔴 HIGH RISK DETECTED: PID={pid} Process={comm} Risk={risk_score:.1f} Anomaly={anomaly_score:.1f}")
                        else:
                            logger.debug(f"⏳ Suppressing high-risk detection during warm-up (PID={pid}, Risk={risk_score:.1f})")
                        logger.warning(f"   Threshold: {threshold:.1f} | Base Risk: {base_risk_score:.1f} | "
                                     f"Connection Bonus: {connection_risk_bonus:.1f} | Total Syscalls: {proc.get('total_syscalls', 0)}")
                        logger.warning(f"   Recent syscalls: {', '.join(list(proc['syscalls'])[-10:])}")
                        if process_info:
                            logger.warning(f"   Process resources: CPU={process_info.get('cpu_percent', 0):.1f}% "
                                         f"Memory={process_info.get('memory_percent', 0):.1f}% "
                                         f"Threads={process_info.get('num_threads', 0)}")
                        
                        # Automated response (if enabled and configured)
                        if self.response_handler and self.response_handler.enabled:
                            reason = f"High risk score: {risk_score:.1f}, Anomaly: {anomaly_score:.1f}"
                            if connection_risk_bonus > 0:
                                reason += f", Connection pattern detected"
                            action = self.response_handler.take_action(
                                pid=pid,
                                process_name=comm,
                                risk_score=risk_score,
                                anomaly_score=anomaly_score,
                                reason=reason
                            )
                            if action:
                                logger.warning(f"   🛡️  Response action taken: {action.value}")
                        
                        # Update cooldown
                        self.alert_cooldown[pid] = current_time
                
                # Also log anomalies even if risk is low (higher threshold to reduce false positives)
                # Only log if anomaly score is significantly high AND is_anomaly flag is set
                # Lowered threshold to 60.0 to improve detection sensitivity
                # Log anomaly detection - lowered threshold to 60 for better sensitivity
                # FIX: Use stored is_anomaly flag and anomaly_score from proc dict
                # Check if ML has run for this process (is_anomaly will be set if ML ran)
                is_anomaly = proc.get('is_anomaly', False)
                stored_anomaly_score = proc.get('anomaly_score', 0.0)
                # Use stored score if available and > 0, otherwise use current anomaly_score
                check_score = stored_anomaly_score if stored_anomaly_score > 0 else anomaly_score
                # Log if: (1) is_anomaly is True AND (2) score >= 60
                # Debug: Log why we're not logging
                if stored_anomaly_score >= 60.0 and not is_anomaly:
                    logger.debug(f"⚠️  Anomaly score {stored_anomaly_score:.1f} >= 60 but is_anomaly=False for PID {pid}")
                if is_anomaly and check_score >= 60.0:
                    # Rate limiting: only log if enough time has passed since last alert
                    current_time = time.time()
                    last_alert = self.alert_cooldown.get(pid, 0)
                    # Use shorter cooldown for anomalies (5 seconds) vs high-risk (30 seconds)
                    anomaly_cooldown = 5.0  # 5 seconds between anomaly logs
                    if current_time - last_alert >= anomaly_cooldown:
                        # Check warm-up period - suppress anomalies during startup
                        time_since_startup = time.time() - self.startup_time
                        if time_since_startup >= self.warmup_period_seconds:
                        comm = proc.get('name', 'unknown')
                        
                        # Get recent syscalls for context
                        recent_syscalls = list(proc['syscalls'])[-15:] if len(proc['syscalls']) > 0 else []
                        syscall_counts = Counter(recent_syscalls)
                        top_syscalls = syscall_counts.most_common(5)
                        
                        # Identify high-risk syscalls in recent activity
                        high_risk_syscalls = ['ptrace', 'setuid', 'setgid', 'chroot', 'mount', 'umount', 
                                             'execve', 'clone', 'fork', 'chmod', 'chown', 'unlink', 'rename']
                        detected_risky = [sc for sc, count in top_syscalls if sc in high_risk_syscalls]
                        
                        # Try to get better process name if current one is pid_XXXXX
                        comm = proc.get('name', 'unknown')
                        if comm.startswith('pid_'):
                            try:
                                p = psutil.Process(pid)
                                better_name = p.name()
                                if better_name and not better_name.startswith('pid_'):
                                    comm = better_name
                                    proc['name'] = better_name  # Update stored name
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                pass
                        # Enhanced anomaly logging with specific details
                        explanation = proc.get('anomaly_explanation', 'Anomalous behavior detected')
                        confidence = proc.get('anomaly_confidence', 0.0)
                        logger.warning(f"🤖 ANOMALY DETECTED: PID={pid} Process={comm} AnomalyScore={anomaly_score:.1f} Risk={risk_score:.1f}")
                        else:
                            logger.debug(f"⏳ Suppressing anomaly detection during warm-up (PID={pid}, Score={check_score:.1f})")
                        logger.warning(f"   ┌─ What's Anomalous:")
                        logger.warning(f"   │  {explanation}")
                        logger.warning(f"   │  Confidence: {confidence:.2f} | Risk Score: {risk_score:.1f}")
                        logger.warning(f"   ├─ Process Activity:")
                        logger.warning(f"   │  Total Syscalls: {proc.get('total_syscalls', 0)} | Recent: {len(recent_syscalls)}")
                        
                        # Automated response for anomalies (if enabled and risk is high enough)
                        if self.response_handler and self.response_handler.enabled:
                            # Only take action if both anomaly AND risk are high
                            if anomaly_score >= 70.0 and risk_score >= 70.0:
                                reason = f"ML anomaly detected: {anomaly_score:.1f}, Risk: {risk_score:.1f}"
                                action = self.response_handler.take_action(
                                    pid=pid,
                                    process_name=comm,
                                    risk_score=risk_score,
                                    anomaly_score=anomaly_score,
                                    reason=reason
                                )
                                if action:
                                    logger.warning(f"   🛡️  Response action taken: {action.value}")
                        
                        if top_syscalls:
                            top_str = ", ".join([f"{sc}({count})" for sc, count in top_syscalls])
                            logger.warning(f"   │  Top Syscalls: {top_str}")
                        if detected_risky:
                            logger.warning(f"   │  ⚠️  High-Risk Syscalls Detected: {', '.join(detected_risky)}")
                        if process_info:
                            logger.warning(f"   │  Resources: CPU={process_info.get('cpu_percent', 0):.1f}% "
                                         f"Memory={process_info.get('memory_percent', 0):.1f}% "
                                         f"Threads={process_info.get('num_threads', 0)}")
                        if recent_syscalls:
                            recent_str = ", ".join(recent_syscalls[-10:])  # Last 10 syscalls
                            if len(recent_str) > 80:
                                recent_str = recent_str[:77] + "..."
                            logger.warning(f"   └─ Recent Sequence: {recent_str}")
                        else:
                            logger.warning(f"   └─ No recent syscalls recorded")
                        
                        # Update cooldown
                        self.alert_cooldown[pid] = current_time
        
        except AttributeError as e:
            # Missing attribute in event
            logger.error(f"❌ AttributeError processing event for PID={event.pid if hasattr(event, 'pid') else 'unknown'}: {e}")
            logger.error(f"   Event object may be malformed. Traceback: {traceback.format_exc()}")
        except KeyError as e:
            # Missing key in dictionary
            logger.error(f"❌ KeyError processing event for PID={event.pid if hasattr(event, 'pid') else 'unknown'}: {e}")
            logger.error(f"   Missing key in process data. Traceback: {traceback.format_exc()}")
        except ValueError as e:
            # Invalid value
            logger.error(f"❌ ValueError processing event for PID={event.pid if hasattr(event, 'pid') else 'unknown'}: {e}")
            logger.error(f"   Invalid data in event. Traceback: {traceback.format_exc()}")
        except Exception as e:
            # Log errors but don't crash the agent
            logger.error(f"❌ Unexpected error processing event for PID={event.pid if hasattr(event, 'pid') else 'unknown'}: {type(e).__name__}: {e}")
            logger.error(f"   Full traceback: {traceback.format_exc()}")
    
    def _count_recent_detections(self, detection_times: deque, window_seconds: int = 300) -> int:
        """Count detections in the last window_seconds (default 5 minutes)"""
        if not detection_times:
            return 0
        current_time = time.time()
        return sum(1 for ts in detection_times if current_time - ts < window_seconds)
    
    def create_dashboard(self) -> Panel:
        """Create dashboard view"""
        with self.processes_lock:
            # Create table with better formatting
            table = Table(
                title="🛡️ Security Agent - Live Monitoring",
                show_header=True,
                header_style="bold cyan",
                box=box.ROUNDED,
                border_style="blue",
                title_style="bold green"
            )
            table.add_column("PID", style="cyan", width=7, justify="right", no_wrap=True)
            table.add_column("Process", style="bright_green", width=20, overflow="ellipsis")
            table.add_column("Risk", style="yellow", width=8, justify="right", no_wrap=True)
            table.add_column("Anomaly", style="magenta", width=9, justify="right", no_wrap=True)
            table.add_column("Syscalls", style="bright_blue", width=10, justify="right", no_wrap=True)
            table.add_column("Recent Syscalls", style="cyan", width=40, overflow="ellipsis")
            table.add_column("Last", style="dim", width=6, justify="right", no_wrap=True)
            
            # Filter out excluded processes from display
            current_time = time.time()
            filtered_procs = [
                (pid, proc) for pid, proc in self.processes.items()
                if proc.get('name', '').lower() not in [p.lower() for p in self.excluded_process_names]
            ]
            
            # Sort by risk score, but also show recently active processes
            sorted_procs = sorted(
                filtered_procs,
                key=lambda x: (
                    x[1]['risk_score'],  # Primary: risk score
                    current_time - x[1].get('last_update', 0)  # Secondary: recency (negative for reverse)
                ),
                reverse=True
            )[:30]  # Top 30 (increased to show more processes)
            
            # Add processes or "Waiting for data..." message
            if sorted_procs:
                for pid, proc in sorted_procs:
                    risk = proc['risk_score']
                    risk_style = "red" if risk >= 50 else "yellow" if risk >= 30 else "green"
                    
                    # Check if process is still alive (recently active)
                    time_since_update = current_time - proc.get('last_update', 0)
                    is_active = time_since_update < 5.0  # Active if updated in last 5 seconds
                    
                    # Format process name - show real name, truncate if too long
                    process_name = proc.get('name', 'unknown')
                    # Remove 'pid_' prefix if it's still there
                    if process_name.startswith('pid_'):
                        process_name = f"<{process_name[4:]}>"  # Show as <PID> if name not found
                    # Truncate long names
                    if len(process_name) > 18:
                        process_name = process_name[:15] + "..."
                    
                    # Add status indicator with better formatting
                    if is_active:
                        status_indicator = "[green]●[/green]"
                    elif time_since_update < 30:
                        status_indicator = "[yellow]○[/yellow]"
                    else:
                        status_indicator = "[dim]○[/dim]"
                    
                    # Get recent syscalls (last 8-10 unique syscalls for better visibility)
                    syscalls_list = list(proc['syscalls'])
                    if syscalls_list:
                        # Get unique recent syscalls (last 12-15, then take up to 10)
                        recent_syscalls = list(dict.fromkeys(syscalls_list[-15:]))[-10:]
                        recent_str = ", ".join(recent_syscalls)
                        # Truncate if too long
                        if len(recent_str) > 38:
                            recent_str = recent_str[:35] + "..."
                    else:
                        recent_str = "[dim]---[/dim]"
                    
                    # Format last update time
                    if time_since_update < 60:
                        last_update_str = f"{int(time_since_update)}s"
                    elif time_since_update < 3600:
                        last_update_str = f"{int(time_since_update/60)}m"
                    else:
                        last_update_str = f"{int(time_since_update/3600)}h"
                    
                    # Format anomaly score with color coding
                    anomaly = proc['anomaly_score']
                    if anomaly >= 50:  # Only high scores are red
                        anomaly_style = "red"
                    elif anomaly >= 40:  # Medium-high scores are yellow
                        anomaly_style = "yellow"
                    else:
                        anomaly_style = "green"  # Everything below 40 is normal (green)
                    
                    # Format syscall count with commas for readability
                    total_syscalls = proc.get('total_syscalls', len(proc['syscalls']))
                    syscalls_str = f"{total_syscalls:,}" if total_syscalls >= 1000 else str(total_syscalls)
                    
                    table.add_row(
                        f"[cyan]{pid}[/cyan]",
                        f"{status_indicator} [bright_green]{process_name}[/bright_green]",
                        f"[{risk_style}]{risk:>6.1f}[/{risk_style}]",
                        f"[{anomaly_style}]{anomaly:>7.2f}[/{anomaly_style}]",
                        f"[bright_blue]{syscalls_str:>9}[/bright_blue]",
                        f"[cyan]{recent_str}[/cyan]",
                        f"[dim]{last_update_str:>5}[/dim]"
                    )
            else:
                # Show info panel when no data yet
                table.add_row(
                    "---",
                    "Waiting for syscalls...",
                    "---",
                    "---",
                    "---",
                    "---",
                    "---"
                )
            
            # Calculate CURRENT stats (not cumulative)
            current_time = time.time()
            current_processes = sum(1 for p in self.processes.values() 
                                   if current_time - p['last_update'] < self.process_timeout)
            current_anomalies = sum(1 for p in self.processes.values() 
                                   if current_time - p['last_update'] < self.process_timeout 
                                   and p.get('anomaly_score', 0) >= 60.0)
            recent_c2 = self._count_recent_detections(self.recent_c2_detections)
            recent_scans = self._count_recent_detections(self.recent_scan_detections)
            
            # Stats with better formatting
            total_syscalls = self.stats['total_syscalls']
            syscalls_formatted = f"{total_syscalls:,}" if total_syscalls >= 1000 else str(total_syscalls)
            stats_text = (
                f"[cyan]Processes:[/cyan] {current_processes} | "
                f"[red]High Risk:[/red] {self.stats['high_risk']} | "
                f"[yellow]Anomalies:[/yellow] {current_anomalies} | "
                f"[magenta]C2:[/magenta] {recent_c2} | "
                f"[yellow]Scans:[/yellow] {recent_scans} | "
                f"[blue]Syscalls:[/blue] {syscalls_formatted}"
            )
            
            # Create info panel explaining scores (show FIRST)
            info_panel = self._create_info_panel()
            
            # Combine info FIRST, then table
            from rich.console import Group
            content = Group(info_panel, table)
            
            return Panel(content, title=stats_text, border_style="green")
    
    def _create_info_panel(self) -> Panel:
        """Create info panel explaining risk and anomaly scores (cached)"""
        # Cache the panel since it doesn't change (reduces blinking)
        if self._info_panel_cache is None:
            threshold = self.config.get('risk_threshold', 30.0)
            
            info_text = f"""
[bold cyan]📊 Score Guide:[/bold cyan]

[bold]Risk Score (0-100):[/bold]
  [green]🟢 0-{threshold:.0f}[/green]   Normal behavior - typical system operations
  [yellow]🟡 {threshold:.0f}-50[/yellow]  Suspicious - unusual patterns detected
  [red]🔴 50-100[/red]  High Risk - potential threat, investigate immediately

[bold]Anomaly Score (ML-based):[/bold]
  [green]0.00-10.00[/green]  Normal - matches learned behavior patterns
  [yellow]10.00-30.00[/yellow]  Unusual - deviates from baseline
  [red]30.00+[/red]      Anomalous - significant deviation, likely threat

[bold]How Scores Work:[/bold]
  • Risk Score: Based on syscall types, frequency, and behavioral patterns
  • Anomaly Score: ML model detects deviations from normal behavior
  • Both scores update in real-time as processes execute syscalls
  • Scores reset when agent restarts (not persisted between runs)

[bold]Current Threshold:[/bold] {threshold:.1f} (configurable with --threshold)
"""
            
            self._info_panel_cache = Panel(info_text.strip(), title="ℹ️  Score Information", border_style="blue")
        
        return self._info_panel_cache
    
    def export_state(self) -> Dict[str, Any]:
        """Export current agent state for web dashboard"""
        current_time = time.time()
        with self.processes_lock:
            # Export all processes with their current state
            processes_data = []
            for pid, proc in self.processes.items():
                # Filter out excluded processes
                proc_name = proc.get('name', 'unknown')
                if proc_name.lower() not in [p.lower() for p in self.excluded_process_names]:
                    # Get recent syscalls for display (last 10, formatted as string)
                    recent_syscalls_list = list(proc.get('syscalls', []))[-10:]
                    recent_syscalls_str = ', '.join(recent_syscalls_list) if recent_syscalls_list else ''
                    
                    processes_data.append({
                        'pid': pid,
                        'name': proc_name,
                        'risk_score': proc.get('risk_score', 0.0),
                        'anomaly_score': proc.get('anomaly_score', 0.0),
                        'total_syscalls': proc.get('total_syscalls', len(proc.get('syscalls', []))),
                        'syscall_count': len(proc.get('syscalls', [])),
                        'recent_syscalls': recent_syscalls_list,  # Last 10 as list
                        'recent_syscalls_str': recent_syscalls_str,  # Last 10 as formatted string
                        'last_update': proc.get('last_update', 0),
                        'time_since_update': current_time - proc.get('last_update', 0)
                    })
            
            # Check if we're still in warm-up period
            time_since_startup = current_time - self.startup_time
            in_warmup = time_since_startup < self.warmup_period_seconds
            
            # During warm-up, suppress high-risk and anomaly counts (but still show processes and syscalls)
            if in_warmup:
                high_risk_count = 0
                anomalies_count = 0
                c2_beacons_count = 0
                port_scans_count = 0
            else:
                high_risk_count = sum(1 for p in processes_data if p['risk_score'] >= self.config.get('risk_threshold', 30.0))
                anomalies_count = sum(1 for p in processes_data if p['anomaly_score'] >= 30.0)
                c2_beacons_count = self._count_recent_detections(self.recent_c2_detections)
                port_scans_count = self._count_recent_detections(self.recent_scan_detections)
            
            state_result = {
                'timestamp': current_time,
                'stats': {
                    'total_processes': len(processes_data),
                    'high_risk': high_risk_count,
                    'anomalies': anomalies_count,
                    'total_syscalls': self.stats['total_syscalls'],
                    'c2_beacons': c2_beacons_count,
                    'port_scans': port_scans_count
                },
                'processes': sorted(processes_data, key=lambda x: x['risk_score'], reverse=True)[:50]  # Top 50
            }
            
            # Debug: Log attack counts (helps verify state file updates)
            if c2_beacons_count > 0 or port_scans_count > 0:
                logger.info(f"📊 State export: c2_beacons={c2_beacons_count}, port_scans={port_scans_count}, total_attacks={c2_beacons_count + port_scans_count}")
            elif len(self.recent_c2_detections) > 0 or len(self.recent_scan_detections) > 0:
                # Log if we have detections but counts are 0 (might be expired or warm-up issue)
                logger.debug(f"State export: Has {len(self.recent_c2_detections)} C2 detections and {len(self.recent_scan_detections)} scan detections, but counts are 0 (may be expired or warm-up)")
            
            return state_result
    
    def _write_state_file(self):
        """Write agent state to JSON file for web dashboard"""
        try:
            state = self.export_state()
            # Log attack counts when writing state file (for debugging)
            stats = state.get('stats', {})
            c2_count = stats.get('c2_beacons', 0)
            port_scan_count = stats.get('port_scans', 0)
            if c2_count > 0 or port_scan_count > 0:
                logger.info(f"📝 Writing state file with attacks: c2_beacons={c2_count}, port_scans={port_scan_count}")
            
            # Always write to /tmp (accessible by all users, including when running as root)
            state_file = Path('/tmp/security_agent_state.json')
            try:
                # Write atomically to prevent corruption: write to temp file, then rename
                temp_file = Path('/tmp/security_agent_state.json.tmp')
                with open(temp_file, 'w') as f:
                    json.dump(state, f, indent=2, ensure_ascii=False)
                # Set permissions
                os.chmod(temp_file, 0o644)
                # Atomic rename (prevents reading partial/corrupted files)
                temp_file.replace(state_file)
                logger.debug(f"State file written: {state_file} ({len(state.get('processes', []))} processes, {c2_count} C2, {port_scan_count} scans)")
            except Exception as e:
                logger.warning(f"Error writing state file to /tmp: {e}")
                # Fallback to user's home if /tmp fails
                try:
                    state_dir = Path.home() / '.cache' / 'security_agent'
                    state_dir.mkdir(parents=True, exist_ok=True)
                    state_file = state_dir / 'agent_state.json'
                    with open(state_file, 'w') as f:
                        json.dump(state, f, indent=2)
                    logger.debug(f"State file written (fallback): {state_file}")
                except Exception as e2:
                    logger.error(f"Error writing state file (both locations failed): {e2}", exc_info=True)
        except Exception as e:
            logger.error(f"Error in _write_state_file: {e}", exc_info=True)
    
    def run_headless(self):
        """Run without dashboard (headless mode for automation)"""
        logger.info("="*60)
        logger.info("Security Agent Starting (Headless Mode)")
        logger.info(f"Log file: {log_file_path}")
        logger.info("="*60)
        
        if not self.start():
            return False
        
        # Start background thread for state file updates (ensures it always runs)
        def state_file_writer():
            """Background thread to continuously write state file"""
            last_write = time.time()
            write_interval = 2.0  # Write every 2 seconds
            write_count = 0
            
            while self.running:
                try:
                    current = time.time()
                    if current - last_write >= write_interval:
                        try:
                            self._write_state_file()
                            last_write = current
                            write_count += 1
                            if write_count % 15 == 0:  # Log every 30 seconds
                                logger.debug(f"State file written #{write_count} ({len(self.processes)} processes, {self.stats['total_syscalls']} syscalls)")
                        except Exception as e:
                            logger.error(f"State file write error: {e}", exc_info=True)
                    time.sleep(0.5)
                except Exception as e:
                    logger.error(f"State file writer thread error: {e}", exc_info=True)
                    time.sleep(1)
        
        # Start state file writer thread
        state_thread = threading.Thread(target=state_file_writer, daemon=True)
        state_thread.start()
        logger.info("✅ State file writer thread started")
        
        # Write initial state file immediately
        try:
            self._write_state_file()
            logger.info("✅ Initial state file written")
        except Exception as e:
            logger.error(f"Failed to write initial state file: {e}", exc_info=True)
        
        try:
            # Main monitoring loop (just keep agent running)
            logger.info("🔄 Starting headless monitoring loop...")
            
            while self.running:
                try:
                    # Just keep the loop running - state file is handled by background thread
                    time.sleep(1)
                except Exception as e:
                    logger.error(f"❌ Error in headless loop: {e}", exc_info=True)
                    time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Agent stopped by user (Ctrl+C)")
        except Exception as e:
            logger.error(f"Fatal error in headless mode: {e}", exc_info=True)
            raise
        finally:
            logger.info("Shutting down agent...")
            self.stop()
            logger.info("Agent shutdown complete")
        
        return True
    
    def run_dashboard(self):
        """Run with dashboard"""
        # Show startup info
        self.console.print("\n[bold green]🛡️  Security Agent Starting...[/bold green]")
        self.console.print("[yellow]ℹ️  Score information will be displayed in the dashboard[/yellow]")
        self.console.print(f"[cyan]📝 Log file: {log_file_path}[/cyan]\n")
        logger.info("="*60)
        logger.info("Security Agent Starting")
        logger.info(f"Log file: {log_file_path}")
        logger.info("="*60)
        time.sleep(2)  # Give user time to read startup message
        
        if not self.start():
            return
        
        try:
            # Use screen=True for better rendering and reduce refresh rate to minimize blinking
            # refresh_per_second=0.5 means update every 2 seconds (much less frequent = no scrolling)
            last_update_time = time.time()
            last_state_write = time.time()  # Track state file writes independently
            last_process_count = 0
            last_total_syscalls = 0
            state_write_interval = 2.0  # Write state every 2 seconds
            
            with Live(self.create_dashboard(), refresh_per_second=0.5, screen=True, transient=False) as live:
                while self.running:
                    # Only update if there are actual changes (prevents constant refreshing)
                    current_time = time.time()
                    current_process_count = len(self.processes)
                    current_total_syscalls = self.stats['total_syscalls']
                    
                    # Update if:
                    # - 3 seconds have passed (minimum refresh rate)
                    # - Process count changed
                    # - Significant syscall count change (>10 new syscalls)
                    should_update = (
                        (current_time - last_update_time >= 3.0) or
                        (current_process_count != last_process_count) or
                        (current_total_syscalls - last_total_syscalls > 10)
                    )
                    
                    if should_update:
                        live.update(self.create_dashboard())
                        last_update_time = current_time
                        last_process_count = current_process_count
                        last_total_syscalls = current_total_syscalls
                    
                    # Write state file periodically for web dashboard sync (independent of dashboard updates)
                    if current_time - last_state_write >= state_write_interval:
                        self._write_state_file()
                        last_state_write = current_time
                    
                    # Sleep to prevent CPU spinning
                    time.sleep(0.5)
        except KeyboardInterrupt:
            logger.info("Agent stopped by user (Ctrl+C)")
        except Exception as e:
            logger.error(f"Fatal error in dashboard: {e}", exc_info=True)
            raise
        finally:
            logger.info("Shutting down agent...")
            self.stop()
            logger.info("Agent shutdown complete")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Simple Security Agent")
    parser.add_argument('--collector', choices=['ebpf', 'auditd'], default='auditd',
                       help='Collector to use (default: auditd)')
    parser.add_argument('--threshold', type=float, default=30.0,
                       help='Risk threshold (default: 30.0)')
    parser.add_argument('--config', type=str, help='Config file path')
    parser.add_argument('--headless', action='store_true',
                       help='Run without dashboard (for automation)')
    parser.add_argument('--with-attacks', action='store_true',
                       help='Run attack simulations automatically (for testing)')
    parser.add_argument('--without-attacks', action='store_true',
                       help='Run without any attack simulations (normal monitoring only)')
    
    args = parser.parse_args()
    
    # Load config
    config = {'collector': args.collector, 'risk_threshold': args.threshold}
    if args.config and os.path.exists(args.config):
        try:
            import yaml
            with open(args.config) as f:
                config.update(yaml.safe_load(f))
        except Exception as e:
            logger.warning(f"Failed to load config: {e}")
    
    # Handle attack simulation options
    attack_thread = None
    if args.with_attacks and not args.without_attacks:
        # Start attack simulation in background thread
        def run_attacks():
            import subprocess
            import sys
            time.sleep(10)  # Wait for agent to start
            logger.info("🎯 Starting attack simulations...")
            try:
                project_root = Path(__file__).parent.parent
                attack_script = project_root / 'scripts' / 'simulate_attacks.py'
                if attack_script.exists():
                    subprocess.run([sys.executable, str(attack_script)], 
                                 cwd=str(project_root), timeout=300)
                    logger.info("✅ Attack simulations completed")
                else:
                    logger.warning(f"⚠️  Attack script not found: {attack_script}")
            except Exception as e:
                logger.error(f"❌ Error running attacks: {e}")
        
        attack_thread = threading.Thread(target=run_attacks, daemon=True)
        attack_thread.start()
        logger.info("🎯 Attack simulations will start in 10 seconds...")
    
    # Create and run agent
    try:
        agent = SimpleSecurityAgent(config)
        if args.headless:
            agent.run_headless()
        else:
            agent.run_dashboard()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"\n❌ Fatal error: {e}")
        print(f"📝 Check log file for details: {log_file_path}")
        sys.exit(1)


if __name__ == '__main__':
    main()

