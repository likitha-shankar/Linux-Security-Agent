#!/bin/bash
# Quick script to test port scanning and C2 beaconing for demo
# Run this on the VM

cd ~/Linux-Security-Agent

echo "=========================================="
echo "  ATTACK DETECTION TEST FOR DEMO"
echo "=========================================="
echo ""

# Check agent is running
if ! ps aux | grep -q '[s]imple_agent'; then
    echo "❌ Agent is not running!"
    echo "Please start it first: bash START_COMPLETE_DEMO.sh"
    exit 1
fi

echo "✅ Agent is running"
echo ""

# Test 1: Port Scanning
echo "=== TEST 1: PORT SCANNING ==="
echo "Running port scan (25 ports)..."
python3 << 'PYEOF'
import socket
import time
for port in range(7000, 7025):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.1)
        s.connect(('localhost', port))
        s.close()
    except:
        pass
    time.sleep(0.04)
print("✅ Port scan completed (25 ports)")
PYEOF

echo "Waiting 15 seconds for detection..."
sleep 15

# Test 2: C2 Beaconing
echo ""
echo "=== TEST 2: C2 BEACONING ==="
echo "Running C2 beaconing (12 beacons, 2.5s intervals, same port)..."
python3 << 'PYEOF'
import socket
import time
target_port = 4444
for i in range(12):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.5)
        s.connect(('localhost', target_port))
        s.close()
    except:
        pass
    print(f"  Beacon {i+1}/12 sent")
    if i < 11:
        time.sleep(2.5)
print("✅ C2 beaconing completed")
PYEOF

echo "Waiting 30 seconds for detection..."
sleep 30

# Check results
echo ""
echo "=== DETECTION RESULTS ==="
LOG=$(ls -t logs/security_agent_*.log 2>/dev/null | head -1)
if [ -n "$LOG" ]; then
    echo "Log file: $(basename $LOG)"
    echo ""
    echo "Detection Counts:"
    echo "  Port Scans: $(grep -c PORT_SCANNING "$LOG" 2>/dev/null || echo 0)"
    echo "  C2 Beaconing: $(grep -c C2_BEACONING "$LOG" 2>/dev/null || echo 0)"
    echo "  High-Risk: $(grep -c 'HIGH RISK DETECTED' "$LOG" 2>/dev/null || echo 0)"
    echo "  Anomalies: $(grep -c 'ANOMALY DETECTED\|🤖 ANOMALY' "$LOG" 2>/dev/null || echo 0)"
    echo ""
    echo "Recent Port Scan Detections:"
    grep 'PORT_SCANNING' "$LOG" 2>/dev/null | tail -2 | sed 's/^/  /' || echo "  None found"
    echo ""
    echo "Recent C2 Beaconing Detections:"
    grep 'C2_BEACONING' "$LOG" 2>/dev/null | tail -2 | sed 's/^/  /' || echo "  None found"
else
    echo "❌ No log file found"
fi

echo ""
echo "=== DASHBOARD STATE ==="
if [ -f /tmp/security_agent_state.json ]; then
    python3 << 'PYEOF'
import json
d = json.load(open('/tmp/security_agent_state.json'))
s = d.get('stats', {})
print(f"Port Scans: {s.get('port_scans', 0)}")
print(f"C2 Beacons: {s.get('c2_beacons', 0)}")
print(f"High Risk: {s.get('high_risk', 0)}")
print(f"Anomalies: {s.get('anomalies', 0)}")
PYEOF
else
    echo "State file not found"
fi

echo ""
echo "=========================================="
echo "  TEST COMPLETE"
echo "=========================================="
