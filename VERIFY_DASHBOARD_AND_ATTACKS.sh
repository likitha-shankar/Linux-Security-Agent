#!/bin/bash
# Complete verification script for dashboard and attack detection
# Run this on the VM after pulling latest code

cd ~/Linux-Security-Agent

echo "=========================================="
echo "  DASHBOARD & ATTACK DETECTION VERIFICATION"
echo "=========================================="
echo ""

# 1. Check and restart dashboard
echo "=== 1. DASHBOARD STATUS ==="
if ps aux | grep -q '[a]pp.py'; then
    echo "✅ Dashboard is running"
    DASH_IP=$(hostname -I | awk '{print $1}')
    echo "   URL: http://$DASH_IP:5001"
else
    echo "⚠️  Dashboard not running - starting..."
    cd web
    pkill -f app.py 2>/dev/null || true
    sleep 2
    nohup python3 app.py >/tmp/dashboard_verify.log 2>&1 &
    sleep 8
    if ps aux | grep -q '[a]pp.py'; then
        echo "✅ Dashboard started"
        DASH_IP=$(hostname -I | awk '{print $1}')
        echo "   URL: http://$DASH_IP:5001"
    else
        echo "❌ Dashboard failed to start"
        tail -10 /tmp/dashboard_verify.log
    fi
    cd ..
fi

echo ""
echo "=== 2. DASHBOARD API TEST ==="
if curl -s http://localhost:5001/api/status >/dev/null 2>&1; then
    echo "✅ Status API: Working"
    curl -s http://localhost:5001/api/status | python3 -m json.tool | head -5
else
    echo "❌ Status API: Not responding"
fi

echo ""
echo "=== 3. AGENT STATUS ==="
if ps aux | grep -q '[s]imple_agent'; then
    echo "✅ Agent is running"
else
    echo "⚠️  Agent not running - starting..."
    sudo pkill -9 -f simple_agent.py 2>/dev/null || true
    sleep 2
    sudo auditctl -a always,exit -F arch=b64 -S socket -S connect -S bind -S accept -S sendto -S recvfrom -k network_syscalls 2>&1 >/dev/null
    sudo nohup python3 core/simple_agent.py --collector auditd --threshold 20 --headless >/tmp/agent_verify.log 2>&1 &
    sleep 12
    if ps aux | grep -q '[s]imple_agent'; then
        echo "✅ Agent started"
    else
        echo "❌ Agent failed to start"
    fi
fi

echo ""
echo "=== 4. TESTING PORT SCANNING DETECTION ==="
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
print("✅ Port scan completed")
PYEOF

echo "Waiting 15 seconds for detection..."
sleep 15

echo ""
echo "=== 5. TESTING C2 BEACONING DETECTION ==="
echo "Running C2 beaconing (12 beacons, 2.5s intervals, same port 4444)..."
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

echo "Waiting 35 seconds for detection..."
sleep 35

echo ""
echo "=== 6. DETECTION RESULTS ==="
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
echo "=== 7. DASHBOARD STATE ==="
if [ -f /tmp/security_agent_state.json ]; then
    python3 << 'PYEOF'
import json
d = json.load(open('/tmp/security_agent_state.json'))
s = d.get('stats', {})
print("Current State:")
print(f"  Port Scans: {s.get('port_scans', 0)}")
print(f"  C2 Beacons: {s.get('c2_beacons', 0)}")
print(f"  High Risk: {s.get('high_risk', 0)}")
print(f"  Anomalies: {s.get('anomalies', 0)}")
print(f"  Processes: {s.get('total_processes', 0)}")
print(f"  Total Syscalls: {s.get('total_syscalls', 0)}")
PYEOF
else
    echo "⚠️  State file not found"
fi

echo ""
echo "=== 8. DASHBOARD WEB INTERFACE ==="
DASH_IP=$(hostname -I | awk '{print $1}')
echo "Dashboard URL: http://$DASH_IP:5001"
if curl -s http://localhost:5001/ | head -5 | grep -q '<!DOCTYPE\|<html'; then
    echo "✅ Dashboard web page accessible"
else
    echo "❌ Dashboard web page not accessible"
fi

echo ""
echo "=========================================="
echo "  VERIFICATION COMPLETE"
echo "=========================================="
echo ""
echo "Summary:"
echo "  - Dashboard: $(if ps aux | grep -q '[a]pp.py'; then echo 'RUNNING'; else echo 'NOT RUNNING'; fi)"
echo "  - Agent: $(if ps aux | grep -q '[s]imple_agent'; then echo 'RUNNING'; else echo 'NOT RUNNING'; fi)"
if [ -n "$LOG" ]; then
    echo "  - Port Scans Detected: $(grep -c PORT_SCANNING "$LOG" 2>/dev/null || echo 0)"
    echo "  - C2 Beacons Detected: $(grep -c C2_BEACONING "$LOG" 2>/dev/null || echo 0)"
fi
echo ""
