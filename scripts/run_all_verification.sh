#!/bin/bash
# Full Demo Verification Script - Run on VM
# Generates detailed log with all commands and results

LOG_FILE="DEMO_VERIFICATION_LOG.txt"

echo "=== DEMO VERIFICATION LOG ===" > "$LOG_FILE"
echo "Generated: $(date)" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

log() {
    echo "$1" | tee -a "$LOG_FILE"
}

log "=== TEST 1: System Check ==="
log "Command: python3 --version"
python3 --version >> "$LOG_FILE" 2>&1
log ""
log "Command: which auditctl"
which auditctl >> "$LOG_FILE" 2>&1
log ""
log "Command: ls -d /sys/kernel/debug/tracing"
ls -d /sys/kernel/debug/tracing >> "$LOG_FILE" 2>&1
log ""

log "=== TEST 2: Stop Old Agents ==="
log "Command: sudo pkill -9 -f simple_agent.py"
sudo pkill -9 -f simple_agent.py >> "$LOG_FILE" 2>&1
sleep 2
log "Command: ps aux | grep simple_agent"
ps aux | grep simple_agent | grep -v grep >> "$LOG_FILE" 2>&1 || log "No agents running"
log ""

log "=== TEST 3: Setup auditd ==="
log "Command: sudo auditctl -a always,exit -F arch=b64 -S socket -S connect -S execve -S fork -S clone -S setuid -S chmod -S chown -k security_syscalls"
sudo auditctl -a always,exit -F arch=b64 -S socket -S connect -S execve -S fork -S clone -S setuid -S chmod -S chown -k security_syscalls >> "$LOG_FILE" 2>&1
log "✅ Auditd rules set"
log ""

log "=== TEST 4: Start Agent ==="
log "Command: nohup sudo python3 core/simple_agent.py --collector auditd --threshold 20 --headless"
nohup sudo python3 core/simple_agent.py --collector auditd --threshold 20 --headless > /tmp/agent_start.log 2>&1 &
AGENT_PID=$!
log "Agent PID: $AGENT_PID"
sleep 10
log "Command: ps aux | grep simple_agent"
ps aux | grep simple_agent | grep -v grep >> "$LOG_FILE" 2>&1
log ""

log "=== TEST 5: Check Agent Logs ==="
LOG=$(ls -t logs/security_agent_*.log 2>/dev/null | head -1)
if [ -n "$LOG" ]; then
    log "Latest log: $LOG"
    log "Command: tail -30 $LOG"
    tail -30 "$LOG" >> "$LOG_FILE" 2>&1
else
    log "No log file found"
fi
log ""

log "=== TEST 6: Run Attack Simulation ==="
log "Command: python3 scripts/simulate_attacks.py"
timeout 120 python3 scripts/simulate_attacks.py >> "$LOG_FILE" 2>&1
log "✅ Attack simulation completed"
log ""

log "=== TEST 7: Check Detections ==="
sleep 20
LOG=$(ls -t logs/security_agent_*.log 2>/dev/null | head -1)
if [ -n "$LOG" ]; then
    log "Checking detections in: $LOG"
    PORT_SCANS=$(grep -c 'PORT_SCANNING' "$LOG" 2>/dev/null || echo "0")
    C2_BEACONS=$(grep -c 'C2_BEACONING' "$LOG" 2>/dev/null || echo "0")
    ANOMALIES=$(grep -c 'ANOMALY DETECTED' "$LOG" 2>/dev/null || echo "0")
    HIGH_RISK=$(grep -c 'HIGH-RISK' "$LOG" 2>/dev/null || echo "0")
    log "Port scans detected: $PORT_SCANS"
    log "C2 beacons detected: $C2_BEACONS"
    log "Anomalies detected: $ANOMALIES"
    log "High-risk processes: $HIGH_RISK"
else
    log "No log file found"
fi
log ""

log "=== TEST 8: Web Dashboard ==="
log "Command: ps aux | grep app.py"
ps aux | grep app.py | grep -v grep >> "$LOG_FILE" 2>&1 || {
    log "Starting dashboard..."
    cd web
    nohup python3 app.py > /tmp/dashboard.log 2>&1 &
    sleep 3
    cd ..
}
log "Command: curl -s http://localhost:5001"
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://localhost:5001 >> "$LOG_FILE" 2>&1
log ""

log "=== TEST 9: Final Status ==="
log "Agent Status:"
ps aux | grep simple_agent | grep -v grep >> "$LOG_FILE" 2>&1 && log "✅ Agent running" || log "❌ Agent not running"
log ""
log "Dashboard Status:"
ps aux | grep app.py | grep -v grep >> "$LOG_FILE" 2>&1 && log "✅ Dashboard running" || log "❌ Dashboard not running"
log ""
log "Port 5001:"
netstat -tlnp 2>/dev/null | grep :5001 >> "$LOG_FILE" 2>&1 && log "✅ Port 5001 listening" || log "❌ Port 5001 not listening"
log ""

log "=== SUMMARY ==="
log "Log file: $LOG_FILE"
log "Lines: $(wc -l < "$LOG_FILE")"
log ""
log "✅ Verification complete!"
log "View full log: cat $LOG_FILE"

cat "$LOG_FILE"
