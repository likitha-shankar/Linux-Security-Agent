#!/usr/bin/env python3
"""
Diagnostic script to check why port scan detection isn't working
"""

import subprocess
import json
from pathlib import Path
import time

def check_agent_running():
    """Check if agent is running"""
    try:
        result = subprocess.run(['pgrep', '-f', 'simple_agent.py'], 
                              capture_output=True, text=True, timeout=2)
        if result.returncode == 0 and result.stdout.strip():
            print(f"✅ Agent is running (PID: {result.stdout.strip()})")
            return True
        else:
            print("❌ Agent is NOT running")
            return False
    except Exception as e:
        print(f"❌ Error checking agent: {e}")
        return False

def check_state_file():
    """Check state file contents"""
    state_file = Path('/tmp/security_agent_state.json')
    if not state_file.exists():
        print("❌ State file does not exist")
        return None
    
    try:
        with open(state_file, 'r') as f:
            state = json.load(f)
        
        stats = state.get('stats', {})
        print(f"\n📊 State file stats:")
        print(f"   Port scans: {stats.get('port_scans', 0)}")
        print(f"   C2 beacons: {stats.get('c2_beacons', 0)}")
        print(f"   Total processes: {stats.get('total_processes', 0)}")
        print(f"   Total syscalls: {stats.get('total_syscalls', 0)}")
        
        return state
    except Exception as e:
        print(f"❌ Error reading state file: {e}")
        return None

def check_logs_for_connections():
    """Check logs for connection-related messages"""
    log_dir = Path('logs')
    if not log_dir.exists():
        print("❌ Logs directory does not exist")
        return
    
    # Get latest log file
    log_files = sorted(log_dir.glob('security_agent_*.log'), key=lambda p: p.stat().st_mtime, reverse=True)
    if not log_files:
        print("❌ No log files found")
        return
    
    latest_log = log_files[0]
    print(f"\n📝 Checking log file: {latest_log.name}")
    
    # Check for network syscalls
    try:
        result = subprocess.run(['sudo', 'grep', '-i', 'NETWORK SYSCALL DETECTED', str(latest_log)], 
                              capture_output=True, text=True, timeout=5)
        network_count = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
        print(f"   Network syscalls detected: {network_count}")
        if network_count > 0:
            print(f"   Last 3 network syscalls:")
            lines = result.stdout.strip().split('\n')[-3:]
            for line in lines:
                print(f"      {line[:100]}")
    except Exception as e:
        print(f"   Error checking network syscalls: {e}")
    
    # Check for connection analysis
    try:
        result = subprocess.run(['sudo', 'grep', '-i', 'Analyzing connection pattern', str(latest_log)], 
                              capture_output=True, text=True, timeout=5)
        analysis_count = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
        print(f"   Connection analyses: {analysis_count}")
        if analysis_count > 0:
            print(f"   Last 3 connection analyses:")
            lines = result.stdout.strip().split('\n')[-3:]
            for line in lines:
                print(f"      {line[:100]}")
    except Exception as e:
        print(f"   Error checking connection analyses: {e}")
    
    # Check for port scan detections
    try:
        result = subprocess.run(['sudo', 'grep', '-i', 'PORT_SCANNING\|Port scan detected', str(latest_log)], 
                              capture_output=True, text=True, timeout=5)
        detection_count = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
        print(f"   Port scan detections in log: {detection_count}")
        if detection_count > 0:
            print(f"   Last 3 detections:")
            lines = result.stdout.strip().split('\n')[-3:]
            for line in lines:
                print(f"      {line[:150]}")
    except Exception as e:
        print(f"   Error checking port scan detections: {e}")
    
    # Check for warm-up period
    try:
        result = subprocess.run(['sudo', 'grep', '-i', 'warm-up\|warmup', str(latest_log)], 
                              capture_output=True, text=True, timeout=5)
        if result.stdout.strip():
            print(f"\n   Warm-up period messages:")
            lines = result.stdout.strip().split('\n')[-5:]
            for line in lines:
                print(f"      {line[:150]}")
    except Exception as e:
        pass

def check_connection_analyzer_state():
    """Try to check connection analyzer internal state (if possible)"""
    print(f"\n🔍 Connection analyzer state:")
    print(f"   (This would require accessing agent internals - not directly accessible)")
    print(f"   Check logs for 'VARYING PORT' or 'Generated port' messages")

def main():
    print("="*60)
    print("🔍 PORT SCAN DETECTION DIAGNOSTIC")
    print("="*60)
    
    # Check agent
    agent_running = check_agent_running()
    
    if not agent_running:
        print("\n⚠️  Agent is not running. Start it first:")
        print("   sudo nohup python3 core/simple_agent.py --collector auditd --threshold 20 --headless >/tmp/agent.log 2>&1 &")
        return
    
    # Check state file
    state = check_state_file()
    
    # Check logs
    check_logs_for_connections()
    
    # Check connection analyzer
    check_connection_analyzer_state()
    
    print("\n" + "="*60)
    print("💡 RECOMMENDATIONS:")
    print("="*60)
    
    if state:
        port_scans = state.get('stats', {}).get('port_scans', 0)
        if port_scans == 0:
            print("1. Port scans showing 0 - check if:")
            print("   - Agent has been running for >30 seconds (warm-up period)")
            print("   - Network syscalls are being captured (check logs)")
            print("   - Connections are being analyzed (check logs)")
            print("   - Ports are being varied (check for 'VARYING PORT' in logs)")
            print("\n2. Try running the attack again and wait 30+ seconds")
            print("3. Check logs in real-time:")
            print("   LATEST_LOG=$(ls -t logs/security_agent_*.log | head -1)")
            print("   sudo tail -f \"$LATEST_LOG\" | grep -E 'NETWORK|connection|PORT_SCAN'")
    else:
        print("1. State file missing - agent may have just started")
        print("2. Wait a few seconds and check again")

if __name__ == '__main__':
    main()
