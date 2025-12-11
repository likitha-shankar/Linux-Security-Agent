#!/bin/bash
# Complete Demo Startup Script
# Run this on the VM to start everything

set -e

cd ~/Linux-Security-Agent

echo "=========================================="
echo "COMPLETE DEMO STARTUP SCRIPT"
echo "=========================================="
echo ""

# Step 1: Verify models are trained
echo "=== STEP 1: Checking ML Models ==="
if [ ! -d ~/.cache/security_agent ] || [ ! -f ~/.cache/security_agent/isolation_forest.pkl ]; then
    echo "⚠️  Models not found. Training now..."
    python3 scripts/train_with_dataset.py --file datasets/adfa_training.json
else
    echo "✅ Models already trained"
    ls -lh ~/.cache/security_agent/*.pkl | head -3
fi
echo ""

# Step 2: Configure auditd
echo "=== STEP 2: Configuring Auditd Rules ==="
sudo auditctl -D 2>/dev/null || true
sudo auditctl -a always,exit -F arch=b64 -S socket -S connect -S bind -S accept -S sendto -S recvfrom -k network_syscalls
echo "✅ Auditd rules configured"
echo ""

# Step 3: Stop any existing processes
echo "=== STEP 3: Stopping Existing Processes ==="
sudo pkill -9 -f simple_agent.py 2>/dev/null || true
pkill -f app.py 2>/dev/null || true
sleep 2
echo "✅ Cleaned up existing processes"
echo ""

# Step 4: Start Agent
echo "=== STEP 4: Starting Security Agent ==="
sudo nohup python3 core/simple_agent.py --collector auditd --threshold 20 --headless >/tmp/agent_demo.log 2>&1 &
sleep 8

if ps aux | grep -q '[s]imple_agent'; then
    AGENT_PID=$(ps aux | grep '[s]imple_agent' | awk '{print $2}' | head -1)
    echo "✅ Agent started with PID: $AGENT_PID"
    tail -5 /tmp/agent_demo.log
else
    echo "❌ Agent failed to start. Check /tmp/agent_demo.log"
    exit 1
fi
echo ""

# Step 5: Start Web Dashboard
echo "=== STEP 5: Starting Web Dashboard ==="
cd web
nohup python3 app.py >/tmp/dashboard_demo.log 2>&1 &
sleep 5

if ps aux | grep -q '[a]pp.py'; then
    DASH_PID=$(ps aux | grep '[a]pp.py' | awk '{print $2}' | head -1)
    echo "✅ Dashboard started with PID: $DASH_PID"
    echo "✅ Dashboard available at: http://$(hostname -I | awk '{print $1}'):5001"
else
    echo "❌ Dashboard failed to start. Check /tmp/dashboard_demo.log"
    exit 1
fi
echo ""

# Step 6: Verify everything is running
echo "=== STEP 6: Verification ==="
sleep 3

# Check agent
if ps aux | grep -q '[s]imple_agent'; then
    echo "✅ Agent: RUNNING"
else
    echo "❌ Agent: NOT RUNNING"
fi

# Check dashboard
if ps aux | grep -q '[a]pp.py'; then
    echo "✅ Dashboard: RUNNING"
    curl -s http://localhost:5001/api/status | python3 -m json.tool | head -5 || echo "⚠️  Dashboard API not responding yet"
else
    echo "❌ Dashboard: NOT RUNNING"
fi

# Check state file
if [ -f /tmp/security_agent_state.json ]; then
    echo "✅ State file: PRESENT"
else
    echo "⚠️  State file: Not created yet (will be created when agent captures syscalls)"
fi

echo ""
echo "=========================================="
echo "✅ DEMO READY!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Wait 30 seconds for normal monitoring"
echo "2. Run: python3 scripts/simulate_attacks.py"
echo "3. Check dashboard: http://$(hostname -I | awk '{print $1}'):5001"
echo "4. View logs: tail -f logs/security_agent_*.log"
echo ""
echo "To stop everything:"
echo "  sudo pkill -f simple_agent.py"
echo "  pkill -f app.py"
echo ""
