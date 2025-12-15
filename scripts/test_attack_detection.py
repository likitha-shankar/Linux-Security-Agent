#!/usr/bin/env python3
"""
Test script to verify attack detection is working
Ensures agent is running and warm-up period has passed before testing
"""

import socket
import time
import os
import sys
import subprocess
import json
from pathlib import Path

def check_agent_running():
    """Check if agent is running"""
    try:
        result = subprocess.run(['pgrep', '-f', 'simple_agent.py'], 
                              capture_output=True, text=True)
        return len(result.stdout.strip()) > 0
    except:
        return False

def wait_for_agent_warmup():
    """Wait for agent to be running and warm-up period to pass"""
    print("⏳ Waiting for agent to be running...")
    max_wait = 60
    waited = 0
    while not check_agent_running() and waited < max_wait:
        time.sleep(2)
        waited += 2
        print(f"   Waiting... ({waited}s)")
    
    if not check_agent_running():
        print("❌ Agent is not running! Please start it first.")
        return False
    
    print("✅ Agent is running")
    print("⏳ Waiting 35 seconds for warm-up period to pass...")
    time.sleep(35)
    print("✅ Ready to test attacks\n")
    return True

def test_port_scanning():
    """Test port scanning detection"""
    print("=" * 60)
    print("🔴 TESTING PORT SCANNING DETECTION")
    print("=" * 60)
    print("Connecting to 30 ports (5000-5030)...")
    
    for port in range(5000, 5030):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.1)
            s.connect(('localhost', port))
            s.close()
        except:
            pass
        time.sleep(0.03)  # 30ms between connections
    
    print("✅ Port scan test completed (30 ports)")
    print("   Waiting 10 seconds for detection...")
    time.sleep(10)

def test_c2_beaconing():
    """Test C2 beaconing detection"""
    print("\n" + "=" * 60)
    print("🔴 TESTING C2 BEACONING DETECTION")
    print("=" * 60)
    print("Sending 15 beacons to port 4444 with 2.5s intervals...")
    
    my_pid = os.getpid()
    print(f"   Process PID: {my_pid}")
    
    for i in range(15):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.5)
            s.connect(('localhost', 4444))
            s.close()
            print(f"   Beacon {i+1}/15 sent")
        except:
            pass
        if i < 14:
            time.sleep(2.5)  # Regular 2.5 second intervals
    
    print("✅ C2 beaconing test completed (15 beacons)")
    print("   Waiting 40 seconds for detection...")
    time.sleep(40)

def check_detection_results():
    """Check detection results from state file"""
    print("\n" + "=" * 60)
    print("📊 CHECKING DETECTION RESULTS")
    print("=" * 60)
    
    state_file = Path('/tmp/security_agent_state.json')
    if not state_file.exists():
        print("❌ State file not found at /tmp/security_agent_state.json")
        return
    
    try:
        with open(state_file, 'r') as f:
            state = json.load(f)
        
        stats = state.get('stats', {})
        port_scans = stats.get('port_scans', 0)
        c2_beacons = stats.get('c2_beacons', 0)
        high_risk = stats.get('high_risk', 0)
        anomalies = stats.get('anomalies', 0)
        
        print(f"\n📈 Current Stats:")
        print(f"   Port Scans: {port_scans}")
        print(f"   C2 Beacons: {c2_beacons}")
        print(f"   High Risk: {high_risk}")
        print(f"   Anomalies: {anomalies}")
        
        if port_scans > 0:
            print(f"\n✅ Port scanning detection: WORKING ({port_scans} detected)")
        else:
            print(f"\n❌ Port scanning detection: NOT WORKING (0 detected)")
        
        if c2_beacons > 0:
            print(f"✅ C2 beaconing detection: WORKING ({c2_beacons} detected)")
        else:
            print(f"❌ C2 beaconing detection: NOT WORKING (0 detected)")
        
        # Check logs
        log_dir = Path(__file__).parent.parent / 'logs'
        if log_dir.exists():
            log_files = sorted(log_dir.glob('security_agent_*.log'), reverse=True)
            if log_files:
                log_file = log_files[0]
                print(f"\n📝 Checking log file: {log_file.name}")
                
                with open(log_file, 'r') as f:
                    log_content = f.read()
                
                port_scan_logs = log_content.count('PORT_SCANNING')
                c2_logs = log_content.count('C2_BEACONING')
                
                print(f"   Port scan detections in log: {port_scan_logs}")
                print(f"   C2 beaconing detections in log: {c2_logs}")
                
                if port_scan_logs > 0 or c2_logs > 0:
                    print("\n   Recent detection entries:")
                    lines = log_content.split('\n')
                    for line in lines[-20:]:
                        if 'PORT_SCANNING' in line or 'C2_BEACONING' in line:
                            print(f"     {line[:100]}...")
        
    except Exception as e:
        print(f"❌ Error reading state file: {e}")

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🔴 ATTACK DETECTION TEST")
    print("=" * 60)
    print()
    
    if not wait_for_agent_warmup():
        sys.exit(1)
    
    # Test port scanning
    test_port_scanning()
    
    # Test C2 beaconing
    test_c2_beaconing()
    
    # Check results
    check_detection_results()
    
    print("\n" + "=" * 60)
    print("✅ TEST COMPLETE")
    print("=" * 60)
