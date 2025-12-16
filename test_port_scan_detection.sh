#!/bin/bash
# Test script to verify port scan detection is working
# Run this on your VM after pulling latest code

set -e

echo "=========================================="
echo "PORT SCAN DETECTION TEST"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

cd ~/Linux-Security-Agent || { echo "Error: Not in Linux-Security-Agent directory"; exit 1; }

echo -e "${BLUE}Step 1: Pulling latest code...${NC}"
git pull
echo ""

echo -e "${BLUE}Step 2: Stopping existing agent...${NC}"
sudo pkill -f simple_agent.py || true
sleep 2
echo ""

echo -e "${BLUE}Step 3: Starting agent with latest code...${NC}"
sudo python3 core/simple_agent.py --collector auditd --threshold 20 --headless >/tmp/agent_test.log 2>&1 &
AGENT_PID=$!
echo "Agent started with PID: $AGENT_PID"
sleep 5

# Verify agent is running
if ! ps -p $AGENT_PID > /dev/null; then
    echo -e "${RED}ERROR: Agent failed to start!${NC}"
    echo "Check /tmp/agent_test.log for errors:"
    tail -20 /tmp/agent_test.log
    exit 1
fi

echo -e "${GREEN}Agent is running${NC}"
echo ""

echo -e "${BLUE}Step 4: Waiting for warm-up period (35 seconds)...${NC}"
for i in {35..1}; do
    echo -ne "\rWaiting: $i seconds remaining..."
    sleep 1
done
echo -e "\rWaiting: 0 seconds remaining... Done!"
echo ""

echo -e "${BLUE}Step 5: Checking initial state (should be clean)...${NC}"
INITIAL_STATE=$(cat /tmp/security_agent_state.json 2>/dev/null | jq -r '.stats.port_scans // 0')
echo "Initial port_scans count: $INITIAL_STATE"
echo ""

echo -e "${BLUE}Step 6: Running port scan attack...${NC}"
python3 -c "from scripts.simulate_attacks import simulate_network_scanning; simulate_network_scanning()"
echo ""

echo -e "${BLUE}Step 7: Waiting 10 seconds for detection...${NC}"
sleep 10
echo ""

echo -e "${BLUE}Step 8: Checking detection results...${NC}"
echo ""

# Get latest log file
LATEST_LOG=$(ls -t logs/security_agent_*.log 2>/dev/null | head -1)

if [ -z "$LATEST_LOG" ]; then
    echo -e "${RED}ERROR: No log file found!${NC}"
    exit 1
fi

echo "Log file: $LATEST_LOG"
echo ""

# Check for port tracking logs
echo -e "${YELLOW}Port tracking logs:${NC}"
sudo grep -E "Port tracking|VARYING PORT|PORT SCAN DETECTED|PORT_SCANNING" "$LATEST_LOG" | tail -20 || echo "No port tracking logs found"
echo ""

# Check for connection analysis
echo -e "${YELLOW}Connection analysis logs:${NC}"
sudo grep -E "Analyzing connection|NETWORK SYSCALL DETECTED" "$LATEST_LOG" | tail -10 || echo "No connection analysis logs found"
echo ""

# Check state file
echo -e "${YELLOW}State file results:${NC}"
FINAL_STATE=$(cat /tmp/security_agent_state.json 2>/dev/null | jq '.stats')
echo "$FINAL_STATE" | jq '.'
echo ""

PORT_SCANS=$(echo "$FINAL_STATE" | jq -r '.port_scans // 0')
C2_BEACONS=$(echo "$FINAL_STATE" | jq -r '.c2_beacons // 0')
HIGH_RISK=$(echo "$FINAL_STATE" | jq -r '.high_risk // 0')
ANOMALIES=$(echo "$FINAL_STATE" | jq -r '.anomalies // 0')

echo "=========================================="
echo "TEST RESULTS"
echo "=========================================="
echo ""

if [ "$PORT_SCANS" -gt 0 ]; then
    echo -e "${GREEN}✅ SUCCESS: Port scans detected! Count: $PORT_SCANS${NC}"
    RESULT=0
else
    echo -e "${RED}❌ FAILURE: No port scans detected (count: $PORT_SCANS)${NC}"
    RESULT=1
fi

echo "C2 Beacons: $C2_BEACONS"
echo "High Risk Processes: $HIGH_RISK"
echo "Anomalies: $ANOMALIES"
echo ""

if [ $RESULT -eq 1 ]; then
    echo -e "${YELLOW}Debugging information:${NC}"
    echo ""
    echo "1. Check if connections were captured:"
    sudo grep -E "socket|connect" "$LATEST_LOG" | grep -i python | tail -10 || echo "No python socket/connect syscalls found"
    echo ""
    echo "2. Check agent process:"
    ps aux | grep simple_agent | grep -v grep || echo "Agent not running!"
    echo ""
    echo "3. Check for errors in agent log:"
    tail -30 /tmp/agent_test.log | grep -i error || echo "No errors in agent log"
    echo ""
    echo "4. Check auditd rules:"
    sudo auditctl -l | grep -E "socket|connect" || echo "No auditd rules for socket/connect"
    echo ""
fi

# Note: Agent left running for continued monitoring
echo -e "${BLUE}Note: Agent is still running for continued monitoring${NC}"
echo ""

if [ $RESULT -eq 0 ]; then
    echo -e "${GREEN}=========================================="
    echo "TEST PASSED: Port scan detection is working!"
    echo "==========================================${NC}"
    exit 0
else
    echo -e "${RED}=========================================="
    echo "TEST FAILED: Port scan detection not working"
    echo "==========================================${NC}"
    exit 1
fi

