#!/usr/bin/env python3
"""
Debug script to check why attack counts are 0 in state file
"""

import json
from pathlib import Path
import subprocess
import re

def check_state_file():
    """Check state file contents"""
    state_file = Path('/tmp/security_agent_state.json')
    if not state_file.exists():
        print("❌ State file not found")
        return
    
    with open(state_file, 'r') as f:
        state = json.load(f)
    
    stats = state.get('stats', {})
    print("📊 State File Stats:")
    print(f"   Port Scans: {stats.get('port_scans', 0)}")
    print(f"   C2 Beacons: {stats.get('c2_beacons', 0)}")
    print(f"   Timestamp: {state.get('timestamp', 'N/A')}")
    print()

def check_logs():
    """Check log file for detection patterns"""
    log_dir = Path(__file__).parent.parent / 'logs'
    if not log_dir.exists():
        print("❌ Logs directory not found")
        return
    
    log_files = sorted(log_dir.glob('security_agent_*.log'), reverse=True)
    if not log_files:
        print("❌ No log files found")
        return
    
    log_file = log_files[0]
    print(f"📝 Checking log: {log_file.name}")
    print()
    
    with open(log_file, 'r') as f:
        content = f.read()
    
    # Count detections
    port_scan_count = content.count('PORT_SCANNING')
    c2_count = content.count('C2_BEACONING')
    
    print(f"Detection counts in log:")
    print(f"   PORT_SCANNING: {port_scan_count}")
    print(f"   C2_BEACONING: {c2_count}")
    print()
    
    # Find detection entries with timestamps
    print("Recent PORT_SCANNING detections:")
    lines = content.split('\n')
    port_scan_lines = [l for l in lines if 'PORT_SCANNING' in l or 'Port scan detected' in l]
    for line in port_scan_lines[-5:]:
        # Extract timestamp
        match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
        if match:
            print(f"   {match.group(1)}: {line[:100]}...")
    print()
    
    print("Recent C2_BEACONING detections:")
    c2_lines = [l for l in lines if 'C2_BEACONING' in l or 'C2 beaconing detected' in l]
    for line in c2_lines[-5:]:
        match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
        if match:
            print(f"   {match.group(1)}: {line[:100]}...")
    print()
    
    # Check for debug logs about counts
    print("Debug logs about detection counts:")
    debug_lines = [l for l in lines if 'DEBUG.*count' in l or 'recent count' in l or 'State export' in l]
    for line in debug_lines[-10:]:
        if 'port_scans' in line.lower() or 'c2_beacons' in line.lower() or 'count' in line.lower():
            match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
            if match:
                print(f"   {match.group(1)}: {line[:120]}...")
    print()
    
    # Check for warm-up logs
    print("Warm-up period logs:")
    warmup_lines = [l for l in lines if 'warm-up' in l.lower() or 'warmup' in l.lower()]
    for line in warmup_lines[-5:]:
        match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
        if match:
            print(f"   {match.group(1)}: {line[:120]}...")

if __name__ == "__main__":
    print("=" * 60)
    print("🔍 DEBUGGING ATTACK COUNTS")
    print("=" * 60)
    print()
    
    check_state_file()
    check_logs()
    
    print("=" * 60)
    print("✅ Debug complete")
    print("=" * 60)
