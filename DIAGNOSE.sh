#!/bin/bash
# Comprehensive diagnostic script for demo troubleshooting
# Run this during demo if something isn't working

echo "=========================================="
echo "COMPREHENSIVE SYSTEM DIAGNOSTIC"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

cd ~/Linux-Security-Agent 2>/dev/null || cd /home/*/Linux-Security-Agent 2>/dev/null || { echo "Error: Cannot find Linux-Security-Agent directory"; exit 1; }

echo -e "${BLUE}=== 1. Agent Status ===${NC}"
if ps aux | grep -E "simple_agent|python.*simple_agent" | grep -v grep > /dev/null; then
    echo -e "${GREEN}✅ Agent is RUNNING${NC}"
    ps aux | grep -E "simple_agent|python.*simple_agent" | grep -v grep
else
    echo -e "${RED}❌ Agent is NOT running${NC}"
fi
echo ""

echo -e "${BLUE}=== 2. Dashboard Status ===${NC}"
if ps aux | grep -E "app.py|flask" | grep -v grep > /dev/null; then
    echo -e "${GREEN}✅ Dashboard is RUNNING${NC}"
    ps aux | grep -E "app.py|flask" | grep -v grep
else
    echo -e "${RED}❌ Dashboard is NOT running${NC}"
fi
echo ""

echo -e "${BLUE}=== 3. Auditd Rules ===${NC}"
sudo auditctl -l | grep -E "socket|connect|sendto|recvfrom" || echo "No network syscall rules found"
echo ""

echo -e "${BLUE}=== 4. Current State File ===${NC}"
if [ -f /tmp/security_agent_state.json ]; then
    cat /tmp/security_agent_state.json | jq '.stats' 2>/dev/null || cat /tmp/security_agent_state.json
else
    echo -e "${RED}State file not found${NC}"
fi
echo ""

echo -e "${BLUE}=== 5. Latest Log File ===${NC}"
LATEST_LOG=$(ls -t logs/security_agent_*.log 2>/dev/null | head -1)
if [ -n "$LATEST_LOG" ]; then
    echo "Log: $LATEST_LOG"
    echo "Size: $(du -h "$LATEST_LOG" | cut -f1)"
    echo "Last modified: $(stat -c %y "$LATEST_LOG" 2>/dev/null || stat -f %Sm "$LATEST_LOG" 2>/dev/null)"
else
    echo -e "${RED}No log file found${NC}"
fi
echo ""

echo -e "${BLUE}=== 6. Recent Network Syscalls (last 10) ===${NC}"
if [ -n "$LATEST_LOG" ]; then
    sudo grep "NETWORK SYSCALL DETECTED" "$LATEST_LOG" | tail -10 || echo "No network syscalls found"
else
    echo "No log file available"
fi
echo ""

echo -e "${BLUE}=== 7. Connection Analysis (last 10) ===${NC}"
if [ -n "$LATEST_LOG" ]; then
    sudo grep "Analyzing connection" "$LATEST_LOG" | tail -10 || echo "No connection analysis found"
else
    echo "No log file available"
fi
echo ""

echo -e "${BLUE}=== 8. Port Generation (last 10) ===${NC}"
if [ -n "$LATEST_LOG" ]; then
    sudo grep -E "Generated port|VARYING PORT" "$LATEST_LOG" | tail -10 || echo "No port generation found"
else
    echo "No log file available"
fi
echo ""

echo -e "${BLUE}=== 9. Port Tracking (last 10) ===${NC}"
if [ -n "$LATEST_LOG" ]; then
    sudo grep "Port tracking" "$LATEST_LOG" | tail -10 || echo "No port tracking found"
else
    echo "No log file available"
fi
echo ""

echo -e "${BLUE}=== 10. Attack Detections (last 10) ===${NC}"
if [ -n "$LATEST_LOG" ]; then
    sudo grep -E "PORT_SCANNING|C2_BEACONING|PORT SCAN DETECTED|Port scan detected" "$LATEST_LOG" | tail -10 || echo "No attack detections found"
else
    echo "No log file available"
fi
echo ""

echo -e "${BLUE}=== 11. Recent Errors (last 10) ===${NC}"
if [ -n "$LATEST_LOG" ]; then
    sudo grep -iE "error|exception|traceback|failed" "$LATEST_LOG" | tail -10 || echo "No errors found"
else
    echo "No log file available"
fi
echo ""

echo -e "${BLUE}=== 12. Agent Log (last 20 lines) ===${NC}"
if [ -f /tmp/agent.log ]; then
    tail -20 /tmp/agent.log
else
    echo "Agent log not found"
fi
echo ""

echo -e "${BLUE}=== 13. Dashboard Log (last 20 lines) ===${NC}"
if [ -f /tmp/dashboard.log ]; then
    tail -20 /tmp/dashboard.log
else
    echo "Dashboard log not found"
fi
echo ""

echo -e "${BLUE}=== 14. System Resources ===${NC}"
echo "CPU: $(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1"%"}')"
echo "Memory: $(free -h | awk '/^Mem:/ {print $3 "/" $2}')"
echo ""

echo -e "${BLUE}=== 15. Recent Python Processes ===${NC}"
ps aux | grep python | grep -v grep | head -5
echo ""

echo "=========================================="
echo "DIAGNOSTIC COMPLETE"
echo "=========================================="
echo ""
echo "Share this output if you need help troubleshooting"

