# Complete Demo Commands

## Step 1: Start Agent and Dashboard

```bash
cd ~/Linux-Security-Agent

# Clean up any existing processes
sudo pkill -9 -f simple_agent.py || true
pkill -9 -f app.py || true
sudo rm -f /tmp/security_agent_state.json

# Configure auditd rules
sudo auditctl -D 2>/dev/null || true
sudo auditctl -a always,exit -F arch=b64 -S socket -S connect -S bind -S accept -S sendto -S recvfrom -k network_syscalls

# Start agent
sudo nohup python3 core/simple_agent.py --collector auditd --threshold 20 --headless >/tmp/agent_demo.log 2>&1 &

# Wait for agent to start
sleep 12

# Verify agent is running
ps aux | grep '[s]imple_agent' | grep -v grep

# Start dashboard
cd web
nohup python3 app.py >/tmp/dashboard_demo.log 2>&1 &

# Wait for dashboard to start
sleep 8

# Verify dashboard is running
ps aux | grep '[a]pp.py' | grep -v grep

# Check dashboard URL
echo "✅ Dashboard: http://136.112.137.224:5001"
```

---

## Step 2: Normal Monitoring (Simple Commands)

**Wait 40 seconds for warm-up period, then run these commands:**

```bash
cd ~/Linux-Security-Agent

# Get latest log file
LATEST_LOG=$(ls -t logs/security_agent_*.log 2>/dev/null | head -1)
echo "Log file: $LATEST_LOG"

# Run simple commands to generate normal activity
echo "=== Running normal commands ==="
pwd
ls -la
whoami
date
ps aux | head -10
top -b -n 1 | head -20
df -h
free -h
cat /etc/passwd | head -5
```

**While commands run, monitor in another terminal:**

```bash
# Terminal 2: Watch live logs
cd ~/Linux-Security-Agent
LATEST_LOG=$(ls -t logs/security_agent_*.log 2>/dev/null | head -1)
sudo tail -f "$LATEST_LOG" | grep -E "EVENT RECEIVED|SCORE UPDATE|HIGH RISK|ANOMALY"
```

**Check state after normal monitoring:**

```bash
# Check state file
cat /tmp/security_agent_state.json | jq '.stats'

# Check API
curl -s http://localhost:5001/api/agent/state | jq '.stats'

# View processes with risk scores
cat /tmp/security_agent_state.json | jq '.processes[] | {pid, name, risk_score, anomaly_score}' | head -20
```

---

## Step 3: Port Attack Test

```bash
# IMPORTANT: Make sure you're in the root directory (not in web/ subdirectory)
cd ~/Linux-Security-Agent

# IMPORTANT: Make sure agent has been running for >30 seconds (warm-up period)
echo "Checking agent uptime..."
ps -p $(pgrep -f simple_agent.py) -o etime

# Get latest log file
LATEST_LOG=$(ls -t logs/security_agent_*.log 2>/dev/null | head -1)
echo "Log file: $LATEST_LOG"

# Run diagnostic first (optional)
python3 scripts/diagnose_port_scan.py

# Run port scan attack (must be run from root directory)
echo "=== Running port scan attack ==="
python3 -c "from scripts.simulate_attacks import simulate_network_scanning; simulate_network_scanning()"

# Wait 30 seconds for detection (agent needs time to process)
echo "⏳ Waiting 30 seconds for detection..."
sleep 30

# Check detection in logs
echo "=== Port scan detections in log ==="
sudo grep -i "PORT_SCANNING\|Port scan detected" "$LATEST_LOG" | tail -10

# Check for connection analyses
echo "=== Connection analyses in log ==="
sudo grep -i "Analyzing connection pattern\|VARYING PORT" "$LATEST_LOG" | tail -10

# Check state file
echo "=== State file after attack ==="
cat /tmp/security_agent_state.json | jq '.stats'

# Check API
echo "=== Dashboard API after attack ==="
curl -s http://localhost:5001/api/agent/state | jq '.stats'

# Should show port_scans > 0
# If still 0, check logs for:
# - "NETWORK SYSCALL DETECTED" (should see connect syscalls)
# - "Analyzing connection pattern" (should see connection analyses)
# - "VARYING PORT" (should see ports being varied)
# - "Warm-up period" (should be ended)
```

---

## Step 4: High Risk Score Test

```bash
# IMPORTANT: Make sure you're in the root directory
cd ~/Linux-Security-Agent

# Get latest log file
LATEST_LOG=$(ls -t logs/security_agent_*.log 2>/dev/null | head -1)

# Run high-risk attack patterns
echo "=== Running high-risk attack patterns ==="
python3 -c "from scripts.simulate_attacks import simulate_privilege_escalation; simulate_privilege_escalation()"

# Wait 15 seconds
sleep 15

# Check high-risk detections in logs
echo "=== High-risk detections in log ==="
sudo grep -i "HIGH RISK DETECTED\|🔴 HIGH RISK" "$LATEST_LOG" | tail -10

# Check state file
echo "=== State file after high-risk attack ==="
cat /tmp/security_agent_state.json | jq '.stats'

# View high-risk processes
echo "=== High-risk processes ==="
cat /tmp/security_agent_state.json | jq '.processes[] | select(.risk_score >= 20) | {pid, name, risk_score, anomaly_score}' | head -10

# Check API
echo "=== Dashboard API ==="
curl -s http://localhost:5001/api/agent/state | jq '{high_risk: .stats.high_risk, anomalies: .stats.anomalies, port_scans: .stats.port_scans}'
```

---

## Step 5: View Log Records on Terminal

```bash
cd ~/Linux-Security-Agent

# Get latest log file
LATEST_LOG=$(ls -t logs/security_agent_*.log 2>/dev/null | head -1)
echo "Log file: $LATEST_LOG"

# View all recent activity (last 50 lines)
echo "=== Recent activity (last 50 lines) ==="
sudo tail -50 "$LATEST_LOG"

# View only high-risk detections
echo "=== High-risk detections ==="
sudo grep "HIGH RISK DETECTED\|🔴 HIGH RISK" "$LATEST_LOG" | tail -20

# View only anomalies
echo "=== Anomaly detections ==="
sudo grep "ANOMALY DETECTED\|⚠️  ANOMALY" "$LATEST_LOG" | tail -20

# View port scan detections
echo "=== Port scan detections ==="
sudo grep -i "PORT_SCANNING\|Port scan detected" "$LATEST_LOG" | tail -20

# View connection pattern detections
echo "=== Connection pattern detections ==="
sudo grep -i "CONNECTION PATTERN DETECTED" "$LATEST_LOG" | tail -20

# View all syscall events (last 30)
echo "=== Recent syscall events ==="
sudo grep "EVENT RECEIVED" "$LATEST_LOG" | tail -30

# View score updates (last 20)
echo "=== Recent score updates ==="
sudo grep "SCORE UPDATE" "$LATEST_LOG" | tail -20
```

---

## Step 6: View JSON State File

```bash
cd ~/Linux-Security-Agent

# View full state file
echo "=== Full state file ==="
cat /tmp/security_agent_state.json | jq '.'

# View only stats
echo "=== Stats only ==="
cat /tmp/security_agent_state.json | jq '.stats'

# View all processes
echo "=== All processes ==="
cat /tmp/security_agent_state.json | jq '.processes[]'

# View processes sorted by risk score (highest first)
echo "=== Processes sorted by risk (highest first) ==="
cat /tmp/security_agent_state.json | jq '.processes | sort_by(-.risk_score) | .[] | {pid, name, risk_score, anomaly_score, total_syscalls}'

# View only high-risk processes
echo "=== High-risk processes (risk >= 20) ==="
cat /tmp/security_agent_state.json | jq '.processes[] | select(.risk_score >= 20) | {pid, name, risk_score, anomaly_score, recent_syscalls}'

# View processes with anomalies
echo "=== Processes with anomalies (anomaly_score >= 30) ==="
cat /tmp/security_agent_state.json | jq '.processes[] | select(.anomaly_score >= 30) | {pid, name, risk_score, anomaly_score}'

# View attack counts
echo "=== Attack counts ==="
cat /tmp/security_agent_state.json | jq '{port_scans: .stats.port_scans, c2_beacons: .stats.c2_beacons, high_risk: .stats.high_risk, anomalies: .stats.anomalies}'
```

---

## Step 7: Complete Demo Sequence (All-in-One)

```bash
cd ~/Linux-Security-Agent

# === 1. START ===
sudo pkill -9 -f simple_agent.py || true
pkill -9 -f app.py || true
sudo rm -f /tmp/security_agent_state.json
sudo auditctl -D 2>/dev/null || true
sudo auditctl -a always,exit -F arch=b64 -S socket -S connect -S bind -S accept -S sendto -S recvfrom -k network_syscalls
sudo nohup python3 core/simple_agent.py --collector auditd --threshold 20 --headless >/tmp/agent_demo.log 2>&1 &
cd web && nohup python3 app.py >/tmp/dashboard_demo.log 2>&1 &
cd ..
sleep 15
echo "✅ Agent and dashboard started"
echo "Dashboard: http://136.112.137.224:5001"

# === 2. WAIT FOR WARM-UP ===
echo "⏳ Waiting 40 seconds for warm-up..."
sleep 40

# === 3. NORMAL MONITORING ===
echo "=== Normal monitoring ==="
LATEST_LOG=$(ls -t logs/security_agent_*.log 2>/dev/null | head -1)
pwd
ls -la
ps aux | head -10
echo "State file:"
cat /tmp/security_agent_state.json | jq '.stats'
sleep 5

# === 4. PORT SCAN ATTACK ===
echo "=== Port scan attack ==="
cd ~/Linux-Security-Agent  # Ensure we're in root directory
python3 -c "from scripts.simulate_attacks import simulate_network_scanning; simulate_network_scanning()"
sleep 20
echo "Port scan detections:"
sudo grep -i "PORT_SCANNING\|Port scan detected" "$LATEST_LOG" | tail -5
echo "State file:"
cat /tmp/security_agent_state.json | jq '.stats'

# === 5. HIGH-RISK ATTACK ===
echo "=== High-risk attack ==="
cd ~/Linux-Security-Agent  # Ensure we're in root directory
python3 -c "from scripts.simulate_attacks import simulate_privilege_escalation; simulate_privilege_escalation()"
sleep 15
echo "High-risk detections:"
sudo grep -i "HIGH RISK DETECTED" "$LATEST_LOG" | tail -5
echo "State file:"
cat /tmp/security_agent_state.json | jq '.stats'

# === 6. FINAL SUMMARY ===
echo "=== Final Summary ==="
echo "State file:"
cat /tmp/security_agent_state.json | jq '.stats'
echo ""
echo "API:"
curl -s http://localhost:5001/api/agent/state | jq '.stats'
echo ""
echo "High-risk processes:"
cat /tmp/security_agent_state.json | jq '.processes[] | select(.risk_score >= 20) | {pid, name, risk_score}' | head -10
```

---

## Quick Reference Commands

### View Live Logs
```bash
LATEST_LOG=$(ls -t logs/security_agent_*.log 2>/dev/null | head -1)
sudo tail -f "$LATEST_LOG"
```

### View State File
```bash
cat /tmp/security_agent_state.json | jq '.'
```

### View Dashboard API
```bash
curl -s http://localhost:5001/api/agent/state | jq '.stats'
```

### Stop Everything
```bash
sudo pkill -f simple_agent.py
pkill -f app.py
```

---

## Expected Results

After running the demo, you should see:

1. **Normal Monitoring:**
   - `total_processes`: > 0
   - `total_syscalls`: Increasing number

2. **Risk Scoring:**
   - `high_risk`: > 0 (after high-risk attacks)
   - Processes with `risk_score >= 20` in state file

3. **Attack Detection:**
   - `port_scans`: > 0 (after port scan attack)
   - Log entries showing "PORT_SCANNING" or "Port scan detected"

4. **Dashboard:**
   - All numbers match state file
   - Live updates every 2 seconds
   - Recent attacks section shows detections
