#!/bin/bash
# Interactive test script that shows terminal progress and opens dashboard
# This script runs the attack and provides real-time feedback

set -e

echo "=========================================="
echo "ATTACK TEST WITH DASHBOARD MONITORING"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

cd ~/Linux-Security-Agent || { echo "Error: Not in Linux-Security-Agent directory"; exit 1; }

# Get VM IP (try to detect or use default)
VM_IP="${VM_IP:-136.112.137.224}"
DASHBOARD_URL="http://${VM_IP}:5001"

echo -e "${CYAN}Dashboard URL: ${DASHBOARD_URL}${NC}"
echo ""
echo -e "${YELLOW}IMPORTANT: Open the dashboard in your browser now!${NC}"
echo -e "${YELLOW}URL: ${DASHBOARD_URL}${NC}"
echo ""
read -p "Press Enter when you have the dashboard open in your browser..."

echo ""
echo -e "${BLUE}Step 1: Checking agent status...${NC}"
if ! ps aux | grep -E "simple_agent|python.*simple_agent" | grep -v grep > /dev/null; then
    echo -e "${RED}Agent is not running! Starting agent...${NC}"
    sudo pkill -f simple_agent.py || true
    sudo auditctl -D 2>/dev/null || true
    sudo auditctl -a always,exit -F arch=b64 -S socket -S connect -S bind -S accept -S sendto -S recvfrom -k network_syscalls
    sudo nohup python3 core/simple_agent.py --collector auditd --threshold 20 --headless >/tmp/agent.log 2>&1 &
    sleep 5
    echo -e "${GREEN}Agent started${NC}"
else
    echo -e "${GREEN}Agent is running${NC}"
fi

echo ""
echo -e "${BLUE}Step 2: Checking dashboard status...${NC}"
if ! ps aux | grep -E "app.py|flask" | grep -v grep > /dev/null; then
    echo -e "${RED}Dashboard is not running! Starting dashboard...${NC}"
    pkill -f app.py || true
    cd web && nohup python3 app.py >/tmp/dashboard.log 2>&1 &
    cd ..
    sleep 3
    echo -e "${GREEN}Dashboard started${NC}"
else
    echo -e "${GREEN}Dashboard is running${NC}"
fi

echo ""
echo -e "${BLUE}Step 3: Checking initial state...${NC}"
INITIAL_STATE=$(cat /tmp/security_agent_state.json 2>/dev/null | jq -r '.stats' || echo '{}')
echo "$INITIAL_STATE" | jq '.'
echo ""

echo -e "${YELLOW}=========================================="
echo "WATCH THE DASHBOARD NOW!"
echo "==========================================${NC}"
echo ""
echo -e "${CYAN}Current stats (before attack):${NC}"
echo "$INITIAL_STATE" | jq '{total_processes, high_risk, anomalies, port_scans, c2_beacons, total_syscalls}'
echo ""

read -p "Press Enter to start the port scan attack..."

echo ""
echo -e "${RED}=========================================="
echo "🚨 STARTING PORT SCAN ATTACK 🚨"
echo "==========================================${NC}"
echo ""

# Run attack in background and show progress
python3 -c "from scripts.simulate_attacks import simulate_network_scanning; simulate_network_scanning()" &
ATTACK_PID=$!

echo -e "${YELLOW}Attack running (PID: $ATTACK_PID)${NC}"
echo ""

# Monitor state file and show updates
echo -e "${CYAN}Monitoring state file updates (watch dashboard too!)...${NC}"
echo ""

for i in {1..30}; do
    sleep 1
    CURRENT_STATE=$(cat /tmp/security_agent_state.json 2>/dev/null | jq -r '.stats' || echo '{}')
    PORT_SCANS=$(echo "$CURRENT_STATE" | jq -r '.port_scans // 0')
    C2_BEACONS=$(echo "$CURRENT_STATE" | jq -r '.c2_beacons // 0')
    HIGH_RISK=$(echo "$CURRENT_STATE" | jq -r '.high_risk // 0')
    ANOMALIES=$(echo "$CURRENT_STATE" | jq -r '.anomalies // 0')
    TOTAL_SYSCALLS=$(echo "$CURRENT_STATE" | jq -r '.total_syscalls // 0')
    
    # Show progress every 3 seconds
    if [ $((i % 3)) -eq 0 ]; then
        echo -ne "\r[${i}s] Port Scans: ${PORT_SCANS} | C2: ${C2_BEACONS} | High Risk: ${HIGH_RISK} | Anomalies: ${ANOMALIES} | Syscalls: ${TOTAL_SYSCALLS}"
    fi
done

echo ""
echo ""

# Wait for attack to complete
wait $ATTACK_PID 2>/dev/null || true

echo ""
echo -e "${BLUE}Step 4: Attack completed. Checking final results...${NC}"
echo ""

# Get latest log file
LATEST_LOG=$(ls -t logs/security_agent_*.log 2>/dev/null | head -1)

if [ -n "$LATEST_LOG" ]; then
    echo -e "${CYAN}Log file: $LATEST_LOG${NC}"
    echo ""
    
    echo -e "${YELLOW}Recent port scan detections:${NC}"
    sudo grep -E "PORT_SCANNING|Port scan detected|PORT SCAN DETECTED" "$LATEST_LOG" | tail -5 || echo "No port scan detections in log"
    echo ""
    
    echo -e "${YELLOW}Port tracking logs:${NC}"
    sudo grep -E "Port tracking|VARYING PORT" "$LATEST_LOG" | tail -10 || echo "No port tracking logs"
    echo ""
fi

# Final state
FINAL_STATE=$(cat /tmp/security_agent_state.json 2>/dev/null | jq -r '.stats' || echo '{}')
echo -e "${CYAN}Final state:${NC}"
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
else
    echo -e "${RED}❌ FAILURE: No port scans detected (count: $PORT_SCANS)${NC}"
fi

echo "C2 Beacons: $C2_BEACONS"
echo "High Risk Processes: $HIGH_RISK"
echo "Anomalies: $ANOMALIES"
echo ""

echo -e "${CYAN}=========================================="
echo "Check your dashboard - it should show:"
echo "- Port Scans: $PORT_SCANS"
echo "- C2 Beacons: $C2_BEACONS"
echo "- High Risk Processes: $HIGH_RISK"
echo "- Anomalies: $ANOMALIES"
echo "==========================================${NC}"
echo ""

echo -e "${YELLOW}Dashboard URL: ${DASHBOARD_URL}${NC}"
echo ""

