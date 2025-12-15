#!/usr/bin/env python3
"""
Web Dashboard for Linux Security Agent
Flask backend with WebSocket support for real-time monitoring
"""

import os
import sys
import json
import subprocess
import threading
import time
import signal
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import sqlite3

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

app = Flask(__name__, template_folder='templates', static_folder=None)
app.config['SECRET_KEY'] = 'security-agent-dashboard-2024'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global state
agent_process = None
agent_thread = None
monitoring_active = False
registered_systems = {}
log_buffer = []

# Database setup
DB_PATH = Path(__file__).parent / 'dashboard.db'

def init_db():
    """Initialize SQLite database for system registration"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS systems (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            hostname TEXT NOT NULL,
            ip_address TEXT,
            description TEXT,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP,
            status TEXT DEFAULT 'offline'
        )
    ''')
    conn.commit()
    conn.close()

def get_systems():
    """Get all registered systems"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT * FROM systems ORDER BY registered_at DESC')
    systems = []
    for row in c.fetchall():
        systems.append({
            'id': row[0],
            'name': row[1],
            'hostname': row[2],
            'ip_address': row[3],
            'description': row[4],
            'registered_at': row[5],
            'last_seen': row[6],
            'status': row[7]
        })
    conn.close()
    return systems

def add_system(name, hostname, ip_address=None, description=None):
    """Register a new system"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO systems (name, hostname, ip_address, description)
        VALUES (?, ?, ?, ?)
    ''', (name, hostname, ip_address, description))
    conn.commit()
    system_id = c.lastrowid
    conn.close()
    return system_id

# Initialize database
init_db()

@app.route('/')
def index():
    """Main dashboard (single page)"""
    return render_template('dashboard.html')

@app.route('/api/logs/list')
def api_list_logs():
    """Get list of available log files (last 10 + current)"""
    project_root = Path(__file__).parent.parent
    possible_log_dirs = [
        project_root / 'logs',
        Path.home() / '.cache' / 'security_agent' / 'logs',
        Path('/root/.cache/security_agent/logs'),
    ]
    
    log_files = []
    for log_dir in possible_log_dirs:
        if log_dir.exists():
            # Get all log files sorted by modification time (newest first)
            all_logs = []
            for log_file in sorted(log_dir.glob('security_agent_*.log'), reverse=True):
                try:
                    stat = log_file.stat()
                    all_logs.append({
                        'filename': log_file.name,
                        'path': str(log_file),
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        'modified_readable': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                    })
                except (OSError, ValueError):
                    continue
            # Only return the last 10 historical files (current/live is handled separately)
            log_files = all_logs[:10]  # Last 10 only
            break  # Use first directory that exists
    
    return jsonify({'logs': log_files})

@app.route('/api/logs/view')
def api_view_log():
    """View a specific log file"""
    log_file = request.args.get('file')
    if not log_file:
        return jsonify({'error': 'No file specified'}), 400
    
    project_root = Path(__file__).parent.parent
    possible_log_dirs = [
        project_root / 'logs',
        Path.home() / '.cache' / 'security_agent' / 'logs',
        Path('/root/.cache/security_agent/logs'),
    ]
    
    log_path = None
    for log_dir in possible_log_dirs:
        if log_dir.exists():
            potential_path = log_dir / log_file
            if potential_path.exists() and potential_path.name.startswith('security_agent_'):
                log_path = potential_path
                break
    
    if not log_path:
        return jsonify({'error': 'Log file not found'}), 404
    
    try:
        # Read last 1000 lines of the log file
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            # Return last 1000 lines
            content = ''.join(lines[-1000:]) if len(lines) > 1000 else ''.join(lines)
        
        return jsonify({
            'filename': log_path.name,
            'content': content,
            'total_lines': len(lines)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/status')
def api_status():
    """Get agent status"""
    global agent_process, monitoring_active
    
    agent_running = False
    agent_pid = None
    
    # First, check if we have a tracked process (started via web)
    if agent_process and agent_process.poll() is None:
        agent_running = True
        agent_pid = agent_process.pid
    else:
        # Check for agent process using pgrep (works for both web-started and manually-started agents)
        try:
            result = subprocess.run(['pgrep', '-f', 'simple_agent.py'], 
                                  capture_output=True, text=True, timeout=2)
            if result.returncode == 0 and result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                # Get the first PID (or most recent if multiple)
                agent_pid = int(pids[0])
                agent_running = True
        except Exception as e:
            # pgrep failed, continue to check log file
            pass
    
    # Also verify with log file check (if process found, verify it's actually writing logs)
    if agent_running:
        # Try multiple possible log file locations (find latest timestamped log)
        project_root = Path(__file__).parent.parent
        possible_log_dirs = [
            project_root / 'logs',
            Path.home() / '.cache' / 'security_agent' / 'logs',
            Path('/root/.cache/security_agent/logs'),
        ]
        
        # Find the latest timestamped log file
        log_file = None
        latest_mtime = 0
        
        for log_dir in possible_log_dirs:
            if log_dir.exists():
                # Check symlink first
                symlink_path = log_dir / 'security_agent.log'
                if symlink_path.exists() and symlink_path.is_symlink():
                    try:
                        real_path = symlink_path.resolve()
                        if real_path.exists():
                            stat = real_path.stat()
                            if stat.st_mtime > latest_mtime:
                                log_file = real_path
                                latest_mtime = stat.st_mtime
                    except (OSError, ValueError):
                        pass
                
                # Check timestamped files
                for log_path in sorted(log_dir.glob('security_agent_*.log'), reverse=True):
                    try:
                        stat = log_path.stat()
                        if stat.st_mtime > latest_mtime:
                            log_file = log_path
                            latest_mtime = stat.st_mtime
                    except (OSError, ValueError):
                        continue
                
                if log_file:
                    break
        
        if log_file is None:
            log_file = possible_log_dirs[0] / 'security_agent.log'
        
        # If log file exists and is recent (modified in last 30 seconds), agent is definitely running
        if log_file and log_file.exists():
            import time
            if time.time() - log_file.stat().st_mtime < 30:
                # Log file is being written to, agent is running
                pass  # Already detected via pgrep
            else:
                # Process exists but log file is stale - might be starting up or issue
                # Still consider it running if process exists
                pass
    
    # If monitoring is active but we haven't detected agent, start monitoring thread
    if agent_running and not monitoring_active:
        monitoring_active = True
        threading.Thread(target=monitor_agent_logs, daemon=True).start()
    
    status = {
        'running': agent_running,
        'monitoring': monitoring_active or agent_running,
        'pid': agent_pid
    }
    return jsonify(status)

@app.route('/api/systems', methods=['GET'])
def api_get_systems():
    """Get all registered systems"""
    systems = get_systems()
    return jsonify(systems)

@app.route('/api/systems', methods=['POST'])
def api_register_system():
    """Register a new system"""
    data = request.json
    system_id = add_system(
        name=data.get('name'),
        hostname=data.get('hostname'),
        ip_address=data.get('ip_address'),
        description=data.get('description')
    )
    return jsonify({'id': system_id, 'message': 'System registered successfully'})

@app.route('/api/agent/start', methods=['POST'])
def api_start_agent():
    """Start the security agent"""
    global agent_process, monitoring_active
    
    if agent_process and agent_process.poll() is None:
        return jsonify({'error': 'Agent already running'}), 400
    
    try:
        # Start agent in headless mode
        project_root = Path(__file__).parent.parent
        log_dir = project_root / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        # Try with sudo first, but handle errors gracefully
        agent_cmd = [
            'sudo', 'python3', 
            str(project_root / 'core' / 'simple_agent.py'),
            '--collector', 'ebpf',
            '--threshold', '20',
            '--headless'
        ]
        
        agent_process = subprocess.Popen(
            agent_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            cwd=str(project_root)
        )
        
        # Wait a moment to check if process started successfully
        time.sleep(2)
        if agent_process.poll() is not None:
            # Process already exited - get error
            try:
                _, stderr_output = agent_process.communicate(timeout=1)
                error_msg = stderr_output if stderr_output else "Agent process exited immediately"
            except:
                error_msg = "Agent failed to start (check sudo permissions and eBPF support)"
            
            socketio.emit('log', {'type': 'error', 'message': f'Agent start failed: {error_msg[:200]}'})
            return jsonify({'error': f'Agent failed to start: {error_msg[:200]}'}), 500
        
        monitoring_active = True
        
        # Start log monitoring thread
        threading.Thread(target=monitor_agent_logs, daemon=True).start()
        
        return jsonify({'message': 'Agent started successfully', 'pid': agent_process.pid})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/agent/state', methods=['GET'])
def api_get_agent_state():
    """Get current agent state (synchronized with terminal dashboard)"""
    try:
        # First, check if agent is currently running.
        # If not running, we should return a fully reset/empty state so the
        # dashboard cards all go to zero when the agent is stopped.
        agent_running = False
        try:
            result = subprocess.run(['pgrep', '-f', 'simple_agent.py'],
                                    capture_output=True, text=True, timeout=2)
            if result.returncode == 0 and result.stdout.strip():
                agent_running = True
        except Exception:
            # If process check fails, fall back to file-based logic below.
            pass

        # If agent is NOT running, reset state and (optionally) clean up stale state files
        if not agent_running:
            project_root = Path(__file__).parent.parent
            possible_state_files = [
                Path('/tmp/security_agent_state.json'),
                Path.home() / '.cache' / 'security_agent' / 'agent_state.json',
                Path('/root/.cache/security_agent/agent_state.json'),
                project_root / '.cache' / 'security_agent' / 'agent_state.json',
            ]

            # Best-effort cleanup of old state files so a fresh dashboard open starts from zero
            for state_path in possible_state_files:
                try:
                    if state_path.exists():
                        state_path.unlink()
                except Exception:
                    # Ignore filesystem errors – API response should still succeed
                    pass

            # Return a fully-reset state (no processes, zero stats)
            return jsonify({
                'processes': [],
                'stats': {
                    'total_processes': 0,
                    'high_risk': 0,
                    'anomalies': 0,
                    'total_syscalls': 0,
                    'c2_beacons': 0,
                    'port_scans': 0,
                }
            }), 200

        # Try multiple possible state file locations
        project_root = Path(__file__).parent.parent
        possible_state_files = [
            Path('/tmp/security_agent_state.json'),  # Shared location (first priority)
            Path.home() / '.cache' / 'security_agent' / 'agent_state.json',
            Path('/root/.cache/security_agent/agent_state.json'),  # When run with sudo
            project_root / '.cache' / 'security_agent' / 'agent_state.json',
        ]
        
        state_file = None
        for state_path in possible_state_files:
            if state_path.exists():
                state_file = state_path
                break
        
        if state_file is None:
            return jsonify({
                'error': 'Agent state not available',
                'message': 'Agent may not be running or state file not found',
                'processes': [],
                'stats': {
                    'total_processes': 0,
                    'high_risk': 0,
                    'anomalies': 0,
                    'total_syscalls': 0,
                    'c2_beacons': 0,
                    'port_scans': 0
                }
            }), 200  # Return 200 with empty state instead of 404
        
        # Read state file
        try:
            with open(state_file, 'r') as f:
                content = f.read()
                # Try to parse JSON
                try:
                    state = json.loads(content)
                except json.JSONDecodeError as json_err:
                    # If JSON is malformed, try to fix common issues or return empty state
                    # Note: logger may not be available in this scope, using print for error reporting
                    print(f"JSON decode error in state file: {json_err}")
                    # Try to find where the error is and truncate there
                    error_pos = json_err.pos if hasattr(json_err, 'pos') else len(content)
                    # Return empty state instead of crashing
                    return jsonify({
                        'error': 'Invalid state file (malformed JSON)',
                        'message': f'JSON error at position {error_pos}: {str(json_err)}',
                        'processes': [],
                        'stats': {
                            'total_processes': 0,
                            'high_risk': 0,
                            'anomalies': 0,
                            'total_syscalls': 0,
                            'c2_beacons': 0,
                            'port_scans': 0
                        }
                    }), 200
        except (IOError, OSError) as e:
            # Note: logger may not be available in this scope, using print for error reporting
            print(f"Error reading state file {state_file}: {e}")
            return jsonify({
                'error': 'Invalid state file',
                'message': str(e),
                'processes': [],
                'stats': {
                    'total_processes': 0,
                    'high_risk': 0,
                    'anomalies': 0,
                    'total_syscalls': 0,
                    'c2_beacons': 0,
                    'port_scans': 0
                }
            }), 200
        
        # Check if state is stale (older than 10 seconds)
        import time
        state_age = time.time() - state.get('timestamp', 0)
        if state_age > 10:
            # Still return state, but mark as stale
            state['_stale'] = True
            state['_stale_age'] = state_age
        
        return jsonify(state)
    except Exception as e:
        # Note: logger may not be available in this scope, using print for error reporting
        print(f"Error reading agent state: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': str(e),
            'processes': [],
            'stats': {
                'total_processes': 0,
                'high_risk': 0,
                'anomalies': 0,
                'total_syscalls': 0,
                'c2_beacons': 0,
                'port_scans': 0
            }
        }), 200  # Return 200 with error instead of 500

@app.route('/api/agent/stop', methods=['POST'])
def api_stop_agent():
    """Stop the security agent"""
    global agent_process, monitoring_active
    
    # First check if agent is actually running (using pgrep, works for both web-started and manually-started)
    agent_running = False
    agent_pid = None
    
    try:
        result = subprocess.run(['pgrep', '-f', 'simple_agent.py'], 
                              capture_output=True, text=True, timeout=2)
        if result.returncode == 0 and result.stdout.strip():
            agent_pids = [int(pid) for pid in result.stdout.strip().split('\n') if pid.strip()]
            if agent_pids:
                agent_running = True
                agent_pid = agent_pids[0]
    except (subprocess.TimeoutExpired, ValueError, FileNotFoundError):
        pass
    
    # If agent is not running, also reset state so dashboard shows zeroed metrics
    if not agent_running:
        try:
            project_root = Path(__file__).parent.parent
            possible_state_files = [
                Path('/tmp/security_agent_state.json'),
                Path.home() / '.cache' / 'security_agent' / 'agent_state.json',
                Path('/root/.cache/security_agent/agent_state.json'),
                project_root / '.cache' / 'security_agent' / 'agent_state.json',
            ]
            for state_path in possible_state_files:
                try:
                    if state_path.exists():
                        state_path.unlink()
                except Exception:
                    pass
        except Exception:
            pass
        return jsonify({'message': 'Agent is already stopped', 'stopped': True, 'state_reset': True})
    
    try:
        # Try to stop the tracked process first (if started via web)
        if agent_process and agent_process.poll() is None:
            agent_process.terminate()
            try:
                agent_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                agent_process.kill()
                agent_process.wait()
        else:
            # Agent was started manually (SSH), kill it using sudo
            if agent_pid:
                try:
                    subprocess.run(['sudo', 'kill', '-INT', str(agent_pid)], 
                                 timeout=5, check=False)
                    # Wait a moment for graceful shutdown
                    time.sleep(2)
                    # If still running, force kill
                    result = subprocess.run(['pgrep', '-f', 'simple_agent.py'], 
                                          capture_output=True, text=True, timeout=2)
                    if result.returncode == 0 and result.stdout.strip():
                        subprocess.run(['sudo', 'kill', '-9', str(agent_pid)], 
                                     timeout=5, check=False)
                except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                    # Try force kill
                    try:
                        subprocess.run(['sudo', 'pkill', '-9', '-f', 'simple_agent.py'], 
                                     timeout=5, check=False)
                    except:
                        pass
        
        # Also kill any remaining processes (cleanup)
        try:
            subprocess.run(['sudo', 'pkill', '-9', '-f', 'simple_agent.py'], 
                          capture_output=True, timeout=5, check=False)
        except:
            pass
        
        agent_process = None
        monitoring_active = False
        
        return jsonify({'message': 'Agent stopped successfully', 'stopped': True})
    except Exception as e:
        # Even if there's an error, try to clean up
        try:
            subprocess.run(['sudo', 'pkill', '-9', '-f', 'simple_agent.py'], 
                          capture_output=True, timeout=5, check=False)
        except:
            pass
        # Also best-effort state reset even on error, so dashboard is consistent
        try:
            project_root = Path(__file__).parent.parent
            possible_state_files = [
                Path('/tmp/security_agent_state.json'),
                Path.home() / '.cache' / 'security_agent' / 'agent_state.json',
                Path('/root/.cache/security_agent/agent_state.json'),
                project_root / '.cache' / 'security_agent' / 'agent_state.json',
            ]
            for state_path in possible_state_files:
                try:
                    if state_path.exists():
                        state_path.unlink()
                except Exception:
                    pass
        except Exception:
            pass
        return jsonify({'error': str(e), 'state_reset': True}), 500

    # After successful stop, clear monitoring flag and reset state files so dashboard starts from zero
    try:
        monitoring_active = False
        project_root = Path(__file__).parent.parent
        possible_state_files = [
            Path('/tmp/security_agent_state.json'),
            Path.home() / '.cache' / 'security_agent' / 'agent_state.json',
            Path('/root/.cache/security_agent/agent_state.json'),
            project_root / '.cache' / 'security_agent' / 'agent_state.json',
        ]
        for state_path in possible_state_files:
            try:
                if state_path.exists():
                    state_path.unlink()
            except Exception:
                pass
    except Exception:
        pass

def monitor_agent_logs():
    """Monitor agent log file and emit updates via WebSocket"""
    global monitoring_active, log_buffer
    
    # Try multiple possible log file locations
    project_root = Path(__file__).parent.parent
    possible_log_dirs = [
        project_root / 'logs',
        Path.home() / '.cache' / 'security_agent' / 'logs',
        Path('/root/.cache/security_agent/logs'),
    ]
    
    # Find the latest timestamped log file (using Chicago timezone naming)
    # Log files are named: security_agent_YYYY-MM-DD_HH-MM-SS.log
    log_file = None
    latest_mtime = 0
    
    for log_dir in possible_log_dirs:
        if log_dir.exists():
            # First try symlink (for backward compatibility)
            symlink_path = log_dir / 'security_agent.log'
            if symlink_path.exists() and symlink_path.is_symlink():
                try:
                    real_path = symlink_path.resolve()
                    if real_path.exists():
                        stat = real_path.stat()
                        if stat.st_mtime > latest_mtime:
                            log_file = real_path
                            latest_mtime = stat.st_mtime
                except (OSError, ValueError):
                    pass
            
            # Also check for timestamped files (find the most recent one)
            for log_path in sorted(log_dir.glob('security_agent_*.log'), reverse=True):
                try:
                    stat = log_path.stat()
                    if stat.st_mtime > latest_mtime:
                        log_file = log_path
                        latest_mtime = stat.st_mtime
                except (OSError, ValueError):
                    continue
            
            if log_file:
                break
    
    # If not found, use default location
    if log_file is None:
        log_file = possible_log_dirs[0] / 'security_agent.log'
    
    # Wait for log file to be created (longer wait for manual starts)
    max_wait = 60
    waited = 0
    while not log_file.exists() and waited < max_wait and monitoring_active:
        time.sleep(1)
        waited += 1
        if waited % 10 == 0:
            socketio.emit('log', {'type': 'info', 'message': f'Waiting for agent logs... ({waited}s) - Start agent manually if needed'})
    
    if not log_file.exists():
        socketio.emit('log', {'type': 'info', 'message': 'No log file found yet. Start the agent manually:'})
        socketio.emit('log', {'type': 'info', 'message': '  sudo python3 core/simple_agent.py --collector ebpf --threshold 20'})
        socketio.emit('log', {'type': 'info', 'message': 'Then refresh this page to see live logs'})
        # Keep monitoring in case file appears later
        while monitoring_active:
            if log_file.exists():
                break
            time.sleep(5)
        if not log_file.exists():
            return
    
    # Track the current file size when monitoring starts
    # Only read entries added AFTER monitoring starts (to avoid showing old attacks/anomalies)
    monitoring_start_time = time.time()
    if log_file.exists():
        try:
            # Check if log file was modified recently (within last 2 minutes)
            # If it's older, assume it's from a previous run and don't read existing content
            file_mtime = log_file.stat().st_mtime
            file_age_seconds = monitoring_start_time - file_mtime

            if file_age_seconds < 120:  # 2 minutes
                # Read only the last few lines (last 50) to show recent startup messages
                # but not old attacks/anomalies
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    all_lines = f.readlines()

                # Only take last 50 lines (should be startup messages, not attacks)
                existing_lines = [l.strip() for l in all_lines[-50:] if l.strip()]

                # Filter out attack/anomaly entries from existing content
                # Only show info/startup messages
                filtered_lines = []
                for line in existing_lines:
                    if 'HIGH RISK DETECTED' not in line and 'ANOMALY DETECTED' not in line:
                        filtered_lines.append(line)

                # Send filtered startup messages to buffer
                for line in filtered_lines:
                    if line:
                        log_entry = parse_log_line(line)
                        if log_entry and log_entry.get('type') not in ('attack', 'anomaly'):
                            log_buffer.append(log_entry)
                            socketio.emit('log', log_entry)
            else:
                # Log file is old (from previous run), don't read existing content
                socketio.emit('log', {'type': 'info', 'message': f'Starting fresh monitoring (log file is {int(file_age_seconds/60)} minutes old)'})
        except Exception:
            socketio.emit('log', {'type': 'info', 'message': 'Starting fresh monitoring'})
    
    # Now monitor for new lines
    try:
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            # Go to end of file (skip existing content we already sent)
            f.seek(0, 2)
            
            while monitoring_active:
                line = f.readline()
                if line:
                    line = line.strip()
                    if line:
                        # Parse log line
                        log_entry = parse_log_line(line)
                        # Skip None entries (filtered out score updates)
                        if log_entry is None:
                            continue
                        
                        log_buffer.append(log_entry)
                        
                        # Keep buffer size manageable
                        if len(log_buffer) > 1000:
                            log_buffer = log_buffer[-500:]
                        
                        # Emit to all connected clients
                        socketio.emit('log', log_entry)
                        
                        # Check for attacks/anomalies
                        if is_attack_or_anomaly(line):
                            socketio.emit('alert', {
                                'type': 'attack' if 'HIGH RISK' in line else 'anomaly',
                                'message': line,
                                'timestamp': datetime.now().isoformat()
                            })
                else:
                    time.sleep(0.5)  # Wait for new lines
    except Exception as e:
        socketio.emit('log', {'type': 'error', 'message': f'Error monitoring log file: {e}'})
        print(f"Error in log monitoring: {e}")

def parse_log_line(line):
    """Parse log line into structured format"""
    entry = {
        'type': 'info',
        'message': line,
        'timestamp': datetime.now().isoformat()
    }
    
    # Include SCORE UPDATE logs but mark them as 'score' type (needed for syscall counting)
    # Dashboard will filter display but still process them for statistics
    if 'SCORE UPDATE' in line:
        entry['type'] = 'score'
        # Still include it so dashboard can extract syscall counts
        # Dashboard will handle filtering for display
    
    # Detect log level (order matters - check more specific first)
    if 'HIGH RISK DETECTED' in line or '🔴 HIGH RISK' in line:
        entry['type'] = 'attack'
    elif 'ANOMALY DETECTED' in line or '⚠️  ANOMALY' in line:
        entry['type'] = 'anomaly'
    elif 'ERROR' in line or '❌' in line:
        entry['type'] = 'error'
    elif 'WARNING' in line or '⚠️' in line:
        entry['type'] = 'warning'
    elif 'INFO' in line or 'ℹ️' in line:
        entry['type'] = 'info'
    
    return entry

def is_attack_or_anomaly(line):
    """Check if log line indicates attack or anomaly"""
    attack_indicators = ['HIGH RISK DETECTED', '🔴', 'ANOMALY DETECTED', '⚠️']
    return any(indicator in line for indicator in attack_indicators)

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    global monitoring_active
    
    emit('status', {'message': 'Connected to security agent dashboard'})
    
    # Start monitoring if not already active
    if not monitoring_active:
        monitoring_active = True
        threading.Thread(target=monitor_agent_logs, daemon=True).start()
    
    # Send recent log buffer
    if log_buffer:
        for entry in log_buffer[-100:]:  # Last 100 entries
            emit('log', entry)

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    pass

if __name__ == '__main__':
    print("="*60)
    print("🛡️  Linux Security Agent - Web Dashboard")
    print("="*60)
    print()
    print("Starting web server...")
    print()
    # Get public IP if on cloud
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except:
        local_ip = "localhost"
    
    print("Access options:")
    print(f"  1. Local: http://localhost:5001")
    print(f"  2. From browser SSH: http://localhost:5001 (in new tab)")
    print(f"  3. Direct (if firewall allows): http://{local_ip}:5001")
    print(f"  4. Public IP: http://136.112.137.224:5001 (if firewall rule added)")
    print()
    print("Press Ctrl+C to stop")
    print("="*60)
    print()
    
    socketio.run(app, host='0.0.0.0', port=5001, debug=False)

