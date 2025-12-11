#!/usr/bin/env python3
"""
Improved Attack Simulation Script
Generates attacks that will be properly detected by the agent
"""

import os
import sys
import time
import subprocess
import socket
from pathlib import Path

def simulate_port_scanning_detected():
    """Simulate port scanning that WILL be detected"""
    print("\n" + "="*60)
    print("🔴 SIMULATING PORT SCANNING ATTACK")
    print("="*60)
    print("This will generate socket/connect syscalls to trigger detection")
    print("Agent needs: 5+ unique ports within 60 seconds")
    print()
    
    # Create a script that makes connections SLOWLY to ensure detection
    # The agent uses simulated ports (8000-8199 range) based on hash of PID+syscall_count+time
    # We need to ensure we generate enough unique syscalls to get 5+ unique simulated ports
    
    attack_script = '''
import socket
import time
import sys

# Make connections slowly to ensure they're tracked
# Each connection generates socket + connect syscalls
# Agent simulates ports based on PID + syscall count + timestamp
# We need to generate enough syscalls to get 5+ unique simulated ports

print("Starting port scan simulation...")
print("Making connections slowly to ensure detection...")

# CRITICAL: Keep process alive and make connections from same PID
# Agent tracks connections per PID, so we need to stay alive long enough
for i in range(15):  # Make 15 connections to ensure 5+ unique simulated ports
    try:
        # Create socket (generates socket syscall)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.5)
        
        # Connect to different ports (generates connect syscall)
        # Agent will simulate ports based on hash of PID+syscall_count+time
        # We need enough syscalls to generate 5+ unique ports
        port = 8000 + (i * 10)  # Use different ports
        sock.connect(('127.0.0.1', port))
        sock.close()
    except (socket.error, ConnectionRefusedError, OSError):
        pass  # Expected - ports not open
    
    # IMPORTANT: Delay between connections to ensure they're tracked separately
    # Also keeps process alive longer so agent can detect pattern
    time.sleep(0.3)
    print(f"Connection attempt {i+1}/15")

# Keep process alive a bit longer to ensure detection completes
print("Waiting for agent to detect pattern...")
time.sleep(2)

print("Port scan simulation complete!")
'''
    
    try:
        proc = subprocess.Popen(
            [sys.executable, '-c', attack_script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = proc.communicate(timeout=30)
        print(stdout.decode())
        if stderr:
            print(stderr.decode())
        print("✅ Port scanning attack simulated")
        print("   Check agent dashboard - should show 'Scans: 1' within 60 seconds")
    except Exception as e:
        print(f"❌ Error: {e}")

def simulate_c2_beaconing_detected():
    """Simulate C2 beaconing that WILL be detected"""
    print("\n" + "="*60)
    print("🔴 SIMULATING C2 BEACONING ATTACK")
    print("="*60)
    print("This will generate periodic connections to trigger detection")
    print("Agent needs: 3+ connections with regular intervals (>5s, <5s variance)")
    print()
    
    attack_script = '''
import socket
import time
import sys

# Make periodic connections with regular intervals
# Agent needs: 3+ connections, mean interval > 5s, stdev < 5s
# CRITICAL: Process must stay alive for all connections to be tracked
print("Starting C2 beaconing simulation...")
print("Making periodic connections every 6 seconds...")
print("Process will stay alive for ~20 seconds to ensure detection...")

for i in range(4):  # Make 4 connections with 6-second intervals
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.5)
        sock.connect(('127.0.0.1', 9000))  # Connect to same port
        sock.close()
        print(f"Beacon {i+1}/4 sent at {time.strftime('%H:%M:%S')}")
    except (socket.error, ConnectionRefusedError, OSError):
        pass  # Expected
    
    if i < 3:  # Don't wait after last connection
        print(f"  Waiting 6 seconds before next beacon...")
        time.sleep(6)  # 6-second intervals (regular, >5s, low variance)

# Keep process alive a bit longer to ensure detection completes
print("Waiting for agent to detect C2 pattern...")
time.sleep(3)

print("C2 beaconing simulation complete!")
'''
    
    try:
        proc = subprocess.Popen(
            [sys.executable, '-c', attack_script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = proc.communicate(timeout=30)
        print(stdout.decode())
        if stderr:
            print(stderr.decode())
        print("✅ C2 beaconing attack simulated")
        print("   Check agent dashboard - should show 'C2: 1' after 3+ connections")
    except Exception as e:
        print(f"❌ Error: {e}")

def simulate_high_risk_process():
    """Simulate high-risk syscalls that will trigger high risk score"""
    print("\n" + "="*60)
    print("🔴 SIMULATING HIGH-RISK PROCESS")
    print("="*60)
    print("This will generate high-risk syscalls (execve, chmod, chown)")
    print()
    
    attack_script = '''
import os
import sys
import time
from pathlib import Path

# Generate high-risk syscalls
temp_dir = Path('/tmp/high_risk_attack')
temp_dir.mkdir(exist_ok=True)

print("Generating high-risk syscalls...")
for i in range(50):
    test_file = temp_dir / f"attack_{i}.tmp"
    
    # Create file (open syscall)
    test_file.write_text("attack data")
    
    # High-risk operations
    try:
        os.chmod(test_file, 0o777)  # chmod (3 points)
        os.chown(test_file, 0, 0)   # chown (3 points) - may fail but generates syscall
    except:
        pass
    
    # Read/write operations
    test_file.read_text()
    test_file.write_text("modified")
    
    # Stat operations
    os.stat(test_file)
    
    time.sleep(0.05)  # Small delay

# Cleanup
for f in temp_dir.glob("attack_*.tmp"):
    f.unlink()
temp_dir.rmdir()

print("High-risk process simulation complete!")
'''
    
    try:
        proc = subprocess.Popen(
            [sys.executable, '-c', attack_script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = proc.communicate(timeout=30)
        print(stdout.decode())
        if stderr:
            print(stderr.decode())
        print("✅ High-risk process simulated")
        print("   Check agent dashboard - should show high risk score (>30)")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    print("="*60)
    print("IMPROVED ATTACK SIMULATION")
    print("="*60)
    print()
    print("This script simulates attacks that WILL be detected by the agent.")
    print("Make sure the agent is running before executing attacks!")
    print()
    
    import sys
    if len(sys.argv) > 1:
        attack_type = sys.argv[1].lower()
        if attack_type == 'port':
            simulate_port_scanning_detected()
        elif attack_type == 'c2':
            simulate_c2_beaconing_detected()
        elif attack_type == 'risk':
            simulate_high_risk_process()
        else:
            print("Unknown attack type. Use: port, c2, or risk")
    else:
        # Run all attacks
        simulate_port_scanning_detected()
        time.sleep(2)
        simulate_high_risk_process()
        time.sleep(2)
        simulate_c2_beaconing_detected()
        
        print("\n" + "="*60)
        print("✅ ALL ATTACKS SIMULATED")
        print("="*60)
        print()
        print("Check the agent dashboard for:")
        print("  - Port Scanning: 'Scans' count should increase")
        print("  - C2 Beaconing: 'C2' count should increase (after 3+ connections)")
        print("  - High Risk: Process with risk score > 30")
        print()

