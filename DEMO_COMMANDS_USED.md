# Demo Commands - Complete Sequence

## Quick Start (All-in-One)

```bash
# 1. Cleanup
cd ~/Linux-Security-Agent
sudo pkill -9 -f simple_agent.py || true
pkill -9 -f app.py || true
sudo rm -f /tmp/security_agent_state.json

# 2. Start Demo
bash START_COMPLETE_DEMO.sh

# 3. Wait for warm-up (40 seconds)
sleep 40

# 4. Run attacks
python3 scripts/simulate_attacks.py

# 5. Check results
cat /tmp/security_agent_state.json | jq '.stats'
curl -s http://localhost:5001/api/agent/state | jq '.stats'
```

---

## Detailed Step-by-Step Commands

### Step 1: Cleanup
```bash
cd ~/Linux-Security-Agent
sudo pkill -9 -f simple_agent.py || true
pkill -9 -f app.py || true
pkill -9 -f START_COMPLETE_DEMO.sh || true
pkill -9 -f "scripts/simulate_attacks.py" || true
sudo rm -f /tmp/security_agent_state.json
```

### Step 2: Start Demo (Agent + Dashboard)
```bash
cd ~/Linux-Security-Agent
bash START_COMPLETE_DEMO.sh
```
**Wait ~25 seconds for startup**

### Step 3: Verify Startup
```bash
# Check agent
ps aux | grep '[s]imple_agent'

# Check dashboard
ps aux | grep '[a]pp.py'

# Test dashboard API
curl -s http://localhost:5001/api/agent/state | jq '.stats'
```

### Step 4: Wait for Warm-up
```bash
# Agent needs 30 seconds warm-up before detecting attacks
sleep 40

# Check current state
curl -s http://localhost:5001/api/agent/state | jq '.stats'
```

### Step 5: Run Attack Simulations
```bash
cd ~/Linux-Security-Agent
python3 scripts/simulate_attacks.py
```

**This will simulate:**
- Port scanning (rapid connections to multiple ports)
- C2 beaconing (regular connections to same port)
- Process churn
- Suspicious file operations
- Ptrace attempts

### Step 6: Check Detection Results
```bash
# State file
cat /tmp/security_agent_state.json | jq '.stats'

# Dashboard API
curl -s http://localhost:5001/api/agent/state | jq '.stats'

# Specific attack counts
cat /tmp/security_agent_state.json | jq -r '.stats.port_scans'
cat /tmp/security_agent_state.json | jq -r '.stats.c2_beacons'
```

### Step 7: View Logs
```bash
# Get latest log file
LATEST_LOG=$(ls -t logs/security_agent_*.log 2>/dev/null | head -1)

# Port scan detections
sudo grep -i 'PORT_SCANNING\|Port scan detected' "$LATEST_LOG" | tail -5

# C2 beaconing detections
sudo grep -i 'C2_BEACONING\|C2 beaconing detected' "$LATEST_LOG" | tail -5

# State file writes
sudo grep 'State BEFORE write|State AFTER write' "$LATEST_LOG" | tail -5
```

### Step 8: Access Dashboard
```bash
# Get VM IP
hostname -I | awk '{print $1}'

# Dashboard URLs:
# - Local:    http://localhost:5001
# - Internal: http://<VM_IP>:5001
# - External: http://136.112.137.224:5001
```

---

## Useful Commands During Demo

### View Live Logs
```bash
LATEST_LOG=$(ls -t logs/security_agent_*.log 2>/dev/null | head -1)
sudo tail -f "$LATEST_LOG"
```

### Monitor Dashboard API
```bash
watch -n 2 'curl -s http://localhost:5001/api/agent/state | jq .stats'
```

### Check Specific Process
```bash
LATEST_LOG=$(ls -t logs/security_agent_*.log 2>/dev/null | head -1)
sudo grep "PID=<PID>" "$LATEST_LOG" | tail -20
```

### View High-Risk Processes
```bash
LATEST_LOG=$(ls -t logs/security_agent_*.log 2>/dev/null | head -1)
sudo grep "HIGH RISK DETECTED" "$LATEST_LOG" | tail -10
```

### View Anomalies
```bash
LATEST_LOG=$(ls -t logs/security_agent_*.log 2>/dev/null | head -1)
sudo grep "ANOMALY DETECTED" "$LATEST_LOG" | tail -10
```

### Stop Everything
```bash
sudo pkill -f simple_agent.py
pkill -f app.py
```

---

## Expected Results

After running attacks, you should see:
- **port_scans**: > 0 (port scanning detected)
- **c2_beacons**: > 0 (C2 beaconing detected)
- **high_risk**: > 0 (high-risk processes)
- **anomalies**: > 0 (ML anomaly detections)
- **total_syscalls**: Increasing number

Dashboard should show:
- Live updates every 2 seconds
- Attack counts in "Attacks" card
- High-risk processes in "High Risk Processes" section
- Recent attacks in "Recent Attacks" section
- Live logs streaming

---

## Troubleshooting

### Dashboard not starting
```bash
# Check if port is in use
ss -tlnp | grep 5001

# Check dashboard log
tail -30 /tmp/dashboard_demo.log

# Start manually
cd ~/Linux-Security-Agent/web
python3 app.py
```

### Agent not detecting attacks
```bash
# Check if agent is running
ps aux | grep '[s]imple_agent'

# Check agent log
tail -50 /tmp/agent_demo.log

# Check latest log file
LATEST_LOG=$(ls -t logs/security_agent_*.log 2>/dev/null | head -1)
tail -50 "$LATEST_LOG"
```

### State file not updating
```bash
# Check state file write logs
LATEST_LOG=$(ls -t logs/security_agent_*.log 2>/dev/null | head -1)
sudo grep 'State BEFORE write|State AFTER write' "$LATEST_LOG" | tail -10

# Check if warm-up period ended
sudo grep 'Warm-up period ended' "$LATEST_LOG" | tail -1
```
