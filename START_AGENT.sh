#!/bin/bash
# Start Agent Script - Run this on the VM

cd ~/Linux-Security-Agent

echo "=== Starting Security Agent ==="

# Kill any existing agents
sudo pkill -9 -f simple_agent.py 2>/dev/null
sleep 2

# Setup auditd
sudo auditctl -a always,exit -F arch=b64 -S socket -S connect -S execve -S fork -S clone -S setuid -S chmod -S chown -k security_syscalls 2>&1 | grep -v "Rule exists"

# Start agent
echo "Starting agent in background..."
sudo nohup python3 core/simple_agent.py --collector auditd --threshold 20 --headless > /tmp/agent.log 2>&1 &

sleep 5

# Check if running
if ps aux | grep -q '[s]imple_agent'; then
    echo "✅ Agent is running!"
    ps aux | grep '[s]imple_agent' | grep -v grep
    echo ""
    echo "Log file: $(ls -t logs/security_agent_*.log 2>/dev/null | head -1)"
    echo ""
    echo "To check status: ps aux | grep simple_agent"
    echo "To view logs: tail -f logs/security_agent_*.log"
else
    echo "❌ Agent failed to start"
    echo "Check logs: tail -20 /tmp/agent.log"
fi
