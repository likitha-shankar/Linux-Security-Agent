#!/bin/bash
# Complete Demo Startup Script
# Run this on the VM to start everything

set -e

cd ~/Linux-Security-Agent

echo "=========================================="
echo " COMPLETE DEMO STARTUP SCRIPT"
echo "=========================================="
echo ""

# Step 1: Verify models are trained
echo "=== STEP 1: Checking ML Models ==="
if [ ! -d ~/.cache/security_agent ] || [ ! -f ~/.cache/security_agent/isolation_forest.pkl ]; then
    echo "[INFO] Models not found. Training now..."
    python3 scripts/train_with_dataset.py --file datasets/adfa_training.json
else
    echo "[OK]   Models already trained"
    ls -lh ~/.cache/security_agent/*.pkl | head -3
fi
echo ""

# Step 2: Configure auditd
echo "=== STEP 2: Configuring eBPF and Auditd Rules ==="
sudo auditctl -D 2>/dev/null || true
sudo auditctl -a always,exit -F arch=b64 -S socket -S connect -S bind -S accept -S sendto -S recvfrom -k network_syscalls
echo "[OK]   eBPF / auditd network rules configured"
echo ""

# Step 3: Stop any existing processes
echo "=== STEP 3: Stopping Existing Processes ==="
sudo pkill -9 -f simple_agent.py 2>/dev/null || true
pkill -f app.py 2>/dev/null || true
sleep 2
echo "[OK]   Cleaned up any existing agent/dashboard processes"
echo ""

# Step 4: Start Agent
echo "=== STEP 4: Starting Security Agent ==="

# First, try to run agent directly to capture any immediate errors
echo "[INFO] Testing agent startup (checking for errors)..."
if sudo python3 core/simple_agent.py --collector auditd --threshold 20 --headless --help >/dev/null 2>&1; then
    echo "[OK]   Agent script is valid"
else
    echo "[WARN] Agent script test failed, but continuing..."
fi

# Start agent in background
echo "[INFO] Starting agent in background..."
sudo nohup python3 core/simple_agent.py --collector auditd --threshold 20 --headless >/tmp/agent_demo.log 2>&1 &
AGENT_START_PID=$!
sleep 10  # Increased wait time to allow agent to initialize

# Check if process is still running
if ps aux | grep -q '[s]imple_agent'; then
    AGENT_PID=$(ps aux | grep '[s]imple_agent' | awk '{print $2}' | head -1)
    echo "[OK]   Agent started with PID: $AGENT_PID"
    echo ""
    echo "------ Last 10 agent log lines (from /tmp/agent_demo.log) ------"
    if [ -f /tmp/agent_demo.log ]; then
        tail -10 /tmp/agent_demo.log || echo "(log file exists but empty)"
    else
        echo "[WARN] Log file /tmp/agent_demo.log not found"
        echo "[INFO] Checking if agent created log file in logs/ directory..."
        LATEST_LOG=$(ls -t logs/security_agent_*.log 2>/dev/null | head -1)
        if [ -n "$LATEST_LOG" ] && [ -f "$LATEST_LOG" ]; then
            echo "[INFO] Found log file: $LATEST_LOG"
            tail -10 "$LATEST_LOG" 2>/dev/null || echo "(log file exists but empty)"
        fi
    fi
    echo "---------------------------------------------------------------"
else
    echo "[ERROR] Agent failed to start or exited immediately"
    echo ""
    echo "------ Error details ------"
    if [ -f /tmp/agent_demo.log ]; then
        echo "Contents of /tmp/agent_demo.log:"
        cat /tmp/agent_demo.log
    else
        echo "[ERROR] Log file /tmp/agent_demo.log not found"
        echo "[INFO] Trying to run agent directly to see error:"
        echo "Running: sudo python3 core/simple_agent.py --collector auditd --threshold 20 --headless"
        sudo timeout 5 python3 core/simple_agent.py --collector auditd --threshold 20 --headless 2>&1 | head -20 || true
    fi
    echo "----------------------------"
    echo ""
    echo "[TROUBLESHOOTING]"
    echo "1. Check Python dependencies: pip3 install -r requirements.txt"
    echo "2. Check if auditd is available: sudo auditctl -l"
    echo "3. Try running manually: sudo python3 core/simple_agent.py --collector auditd --threshold 20 --headless"
    echo "4. Check system logs: sudo dmesg | tail -20"
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
    DASH_IP=$(hostname -I | awk '{print $1}')
    echo "[OK]   Dashboard started with PID: $DASH_PID"
    echo "[OK]   Dashboard available at: http://$DASH_IP:5001"
else
    echo "[ERROR] Dashboard failed to start. Check /tmp/dashboard_demo.log"
    exit 1
fi
echo ""

# Step 6: Verify everything is running
echo "=== STEP 6: Verification ==="
sleep 3

# Check agent
if ps aux | grep -q '[s]imple_agent'; then
    echo "[OK]   Agent: RUNNING"
else
    echo "[WARN] Agent: NOT RUNNING"
fi

# Check dashboard
if ps aux | grep -q '[a]pp.py'; then
    echo "[OK]   Dashboard: RUNNING"
    echo "[INFO] Dashboard /api/status (first 5 lines):"
    curl -s http://localhost:5001/api/status | python3 -m json.tool | head -5 || echo "[WARN] Dashboard API not responding yet"
else
    echo "[WARN] Dashboard: NOT RUNNING"
fi

# Check state file
if [ -f /tmp/security_agent_state.json ]; then
    echo "[OK]   State file: PRESENT (/tmp/security_agent_state.json)"
else
    echo "[WARN] State file: Not created yet (will be created when agent captures syscalls)"
fi

# Step 7: Display log file information
echo ""
echo "=== STEP 7: Log Files ==="
sleep 2  # Give agent time to create log file

# Find the latest log file
LATEST_LOG=$(ls -t logs/security_agent_*.log 2>/dev/null | head -1)
if [ -n "$LATEST_LOG" ] && [ -f "$LATEST_LOG" ]; then
    echo "[OK]   Latest log file: $LATEST_LOG"
    echo "[INFO] Log file size: $(du -h "$LATEST_LOG" | cut -f1)"
    echo ""
    echo "------ Recent log entries (last 10 lines) ------"
    tail -10 "$LATEST_LOG" 2>/dev/null || echo "(log file exists but empty)"
    echo "------------------------------------------------"
    echo ""
    echo "[INFO] To view live logs: tail -f $LATEST_LOG"
    echo "[INFO] To view in dashboard: Open http://$DASH_IP:5001 and check 'Live Logs' section"
else
    echo "[INFO] Log file not created yet (will appear in logs/ directory)"
    echo "[INFO] Log files location: logs/security_agent_YYYY-MM-DD_HH-MM-SS.log"
fi

echo ""
echo "=========================================="
echo " DEMO READY!"
echo "=========================================="
echo ""
echo "Next steps (run these in separate terminals):"
echo "  1) Wait ~30 seconds for normal monitoring"
echo "  2) Run attacks:     python3 scripts/simulate_attacks.py"
echo "  3) Open dashboard:  http://$DASH_IP:5001"
echo "  4) View live logs:  tail -f $LATEST_LOG"
echo "  5) View attacks:    sudo grep -E 'PORT_SCANNING|C2_BEACONING' $LATEST_LOG"
echo ""
echo "Log file commands:"
echo "  - Live tail:        tail -f $LATEST_LOG"
echo "  - View attacks:     sudo grep -E 'PORT_SCANNING|C2_BEACONING' logs/security_agent_*.log"
echo "  - View high-risk:   sudo grep 'HIGH RISK DETECTED' logs/security_agent_*.log"
echo "  - View anomalies:   sudo grep 'ANOMALY DETECTED' logs/security_agent_*.log"
echo ""
echo "To stop everything:"
echo "  sudo pkill -f simple_agent.py"
echo "  pkill -f app.py"
echo ""
echo "[INFO] Script finished. You can now type commands in this terminal."
