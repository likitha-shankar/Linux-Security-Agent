#!/bin/bash
# Test script for terminal dashboard fixes

echo "=== Testing Terminal Dashboard Fixes ==="
echo ""

cd ~/Linux-Security-Agent

echo "1. Pulling latest code..."
git pull origin main
echo ""

echo "2. Stopping any running agents..."
sudo pkill -9 -f 'simple_agent.py' 2>/dev/null
sleep 2
echo "✅ Old agents stopped"
echo ""

echo "3. Starting agent with dashboard (will run for 30 seconds)..."
sudo timeout 30 python3 core/simple_agent.py --collector ebpf --threshold 20 --dashboard 2>&1 | tee /tmp/agent_test_output.txt &
AGENT_PID=$!
echo "Agent PID: $AGENT_PID"
echo ""

echo "4. Waiting 20 seconds for agent to collect data..."
sleep 20
echo ""

echo "5. Checking agent status..."
if ps -p $AGENT_PID > /dev/null 2>&1; then
    echo "✅ Agent is running"
else
    echo "⚠️  Agent stopped (may have completed or errored)"
fi
echo ""

echo "6. Checking recent log output for dashboard stats..."
echo "--- Recent Dashboard Stats ---"
tail -50 logs/security_agent_*.log 2>/dev/null | grep -E "Processes:|High Risk:|Anomalies:|C2:|Scans:" | tail -5 || echo "No dashboard stats found in logs yet"
echo ""

echo "7. Checking for any errors..."
ERRORS=$(tail -100 logs/security_agent_*.log 2>/dev/null | grep -i "error\|exception\|traceback" | wc -l)
if [ "$ERRORS" -eq 0 ]; then
    echo "✅ No errors found in logs"
else
    echo "⚠️  Found $ERRORS potential errors - checking..."
    tail -100 logs/security_agent_*.log 2>/dev/null | grep -i "error\|exception" | tail -3
fi
echo ""

echo "8. Final agent status..."
sleep 5
if ps -p $AGENT_PID > /dev/null 2>&1; then
    echo "✅ Agent still running - stopping it..."
    sudo kill $AGENT_PID 2>/dev/null
    sleep 2
fi

echo ""
echo "=== Test Complete ==="
echo "Check the dashboard output above to verify:"
echo "  - Processes count shows current active processes"
echo "  - Anomalies count shows current anomalous processes"
echo "  - C2/Scans show recent detections (not cumulative)"
echo ""
