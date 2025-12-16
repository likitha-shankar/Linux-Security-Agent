#!/bin/bash
# Run this script on the VM to diagnose port scan detection issues

echo "============================================================"
echo "🔍 PORT SCAN DETECTION DIAGNOSTIC - VM"
echo "============================================================"

cd ~/Linux-Security-Agent

# 1. Check if agent is running
echo ""
echo "1. Checking if agent is running..."
if pgrep -f simple_agent.py > /dev/null; then
    AGENT_PID=$(pgrep -f simple_agent.py)
    echo "✅ Agent is running (PID: $AGENT_PID)"
    # Check uptime
    ps -p $AGENT_PID -o etime= 2>/dev/null | head -1
else
    echo "❌ Agent is NOT running"
    echo "   Start it with: sudo nohup python3 core/simple_agent.py --collector auditd --threshold 20 --headless >/tmp/agent.log 2>&1 &"
    exit 1
fi

# 2. Check state file
echo ""
echo "2. Checking state file..."
if [ -f /tmp/security_agent_state.json ]; then
    echo "✅ State file exists"
    echo "   Current stats:"
    cat /tmp/security_agent_state.json | jq '.stats' 2>/dev/null || echo "   (Error reading JSON)"
else
    echo "❌ State file does not exist"
fi

# 3. Get latest log file
echo ""
echo "3. Checking logs..."
LATEST_LOG=$(ls -t logs/security_agent_*.log 2>/dev/null | head -1)
if [ -z "$LATEST_LOG" ]; then
    echo "❌ No log files found"
else
    echo "✅ Latest log: $LATEST_LOG"
    
    # Check for network syscalls
    echo ""
    echo "   Network syscalls detected:"
    sudo grep -i "NETWORK SYSCALL DETECTED" "$LATEST_LOG" 2>/dev/null | tail -5 | head -3
    
    # Check for connection analyses
    echo ""
    echo "   Connection analyses:"
    sudo grep -i "Analyzing connection pattern" "$LATEST_LOG" 2>/dev/null | tail -5 | head -3
    
    # Check for port variations
    echo ""
    echo "   Port variations (for port scanning):"
    sudo grep -i "VARYING PORT\|Varying port" "$LATEST_LOG" 2>/dev/null | tail -5 | head -3
    
    # Check for port scan detections
    echo ""
    echo "   Port scan detections:"
    PORT_SCAN_COUNT=$(sudo grep -i "PORT_SCANNING\|Port scan detected" "$LATEST_LOG" 2>/dev/null | wc -l)
    echo "   Total in log: $PORT_SCAN_COUNT"
    if [ "$PORT_SCAN_COUNT" -gt 0 ]; then
        sudo grep -i "PORT_SCANNING\|Port scan detected" "$LATEST_LOG" 2>/dev/null | tail -3
    fi
    
    # Check warm-up period
    echo ""
    echo "   Warm-up period status:"
    sudo grep -i "warm-up\|warmup" "$LATEST_LOG" 2>/dev/null | tail -3
fi

# 4. Check connection analyzer state (via logs)
echo ""
echo "4. Checking connection patterns in recent logs..."
if [ -n "$LATEST_LOG" ]; then
    echo "   Recent connection events (last 10):"
    sudo grep -E "NETWORK SYSCALL|Analyzing connection|VARYING PORT|PORT_SCANNING" "$LATEST_LOG" 2>/dev/null | tail -10
fi

# 5. Check if auditd is capturing connect syscalls
echo ""
echo "5. Checking auditd rules..."
sudo auditctl -l 2>/dev/null | grep -E "socket|connect" || echo "   (No socket/connect rules found)"

# 6. Test: Run a quick port scan and monitor
echo ""
echo "6. Testing port scan detection..."
echo "   Running diagnostic port scan..."
python3 -c "from scripts.simulate_attacks import simulate_network_scanning; simulate_network_scanning()" 2>&1

echo ""
echo "   Waiting 10 seconds for detection..."
sleep 10

# Check logs again
if [ -n "$LATEST_LOG" ]; then
    echo ""
    echo "   New detections after test:"
    sudo grep -i "PORT_SCANNING\|Port scan detected" "$LATEST_LOG" 2>/dev/null | tail -3
fi

# Check state file again
echo ""
echo "   State file after test:"
cat /tmp/security_agent_state.json | jq '.stats' 2>/dev/null || echo "   (Error reading JSON)"

echo ""
echo "============================================================"
echo "💡 RECOMMENDATIONS:"
echo "============================================================"
echo "1. If port_scans is still 0:"
echo "   - Check if agent has been running >30 seconds (warm-up period)"
echo "   - Verify network syscalls are being captured"
echo "   - Check if ports are being varied (look for 'VARYING PORT' in logs)"
echo ""
echo "2. To monitor in real-time:"
echo "   LATEST_LOG=\$(ls -t logs/security_agent_*.log | head -1)"
echo "   sudo tail -f \"\$LATEST_LOG\" | grep -E 'NETWORK|connection|PORT_SCAN|VARYING'"
echo ""
echo "3. To run full test:"
echo "   python3 -c \"from scripts.simulate_attacks import simulate_network_scanning; simulate_network_scanning()\""
echo "   sleep 30"
echo "   cat /tmp/security_agent_state.json | jq '.stats'"
