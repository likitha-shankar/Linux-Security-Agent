### 0. Setup / cleanup (VM)

```bash
cd ~/Linux-Security-Agent

# Clean any old runs (safe to run anytime)
sudo pkill -9 -f simple_agent.py || true
pkill -9 -f app.py || true
pkill -9 -f START_COMPLETE_DEMO.sh || true
pkill -9 -f "scripts/simulate_attacks.py" || true
sudo rm -f /tmp/security_agent_state.json
```

---

### 1. Start full demo (agent + dashboard)

```bash
cd ~/Linux-Security-Agent
bash START_COMPLETE_DEMO.sh
```

---

### 2. Run attacks

In **Terminal 2**:

```bash
cd ~/Linux-Security-Agent

# All attacks (recommended)
python3 scripts/simulate_attacks.py

# Only network scanning (extra port scans)
python3 -c "from scripts.simulate_attacks import simulate_network_scanning; simulate_network_scanning()"

# Only C2 beaconing (if you want to try to trigger it live)
python3 -c "from scripts.simulate_attacks import simulate_c2_beaconing; simulate_c2_beaconing()"


cat /tmp/security_agent_state.json | jq '.stats'
```

---

### 3. Quick log views (while demo is running)

```bash
cd ~/Linux-Security-Agent

# Get the latest log file (current session)
LATEST_LOG=$(ls -t logs/security_agent_*.log 2>/dev/null | head -1)

# Live logs (everything) - current log only
sudo tail -f "$LATEST_LOG"

# Only high-risk + anomalies - current log only
sudo tail -f "$LATEST_LOG" | grep -E "HIGH RISK DETECTED|ANOMALY DETECTED"

# Only high-risk (short snapshot) - current log only
sudo grep "HIGH RISK DETECTED" "$LATEST_LOG" | tail -20

# Only anomalies (short snapshot) - current log only
sudo grep "ANOMALY DETECTED" "$LATEST_LOG" | tail -20

# Only network-pattern attacks (port scan + C2) – good for showing T1046 / T1071 - current log only
sudo grep -E "PORT_SCANNING|C2_BEACONING" "$LATEST_LOG" | tail -20

# Debug: Check why attack counts might be 0 (shows detection flow)
sudo grep -E "DEBUG.*Port scan|DEBUG.*C2|DEBUG.*State|Port scan detected|State export|warm-up" "$LATEST_LOG" | tail -30

# Or use the symlink (always points to latest)
sudo tail -f logs/security_agent.log | grep -E "PORT_SCANNING|C2_BEACONING"
```

---

### 4. Check live agent state (what drives the dashboard)

```bash
cd ~/Linux-Security-Agent

# Summary stats (grep for key fields)
curl -s http://localhost:5001/api/agent/state | python3 -m json.tool | \
  grep -E '"total_processes"|"high_risk"|"anomalies"|"total_syscalls"|"port_scans"|"c2_beacons"'

# Full (first 40 lines) for explanation
curl -s http://localhost:5001/api/agent/state | python3 -m json.tool | head -40
```

You can say:
- `port_scans` + `c2_beacons` = Attacks card  
- `total_processes`, `high_risk`, `anomalies`, `total_syscalls` = top cards.

---

### 5. Spot-check a specific process

From dashboard (e.g. `PID 636393`, process `groups`):

```bash
cd ~/Linux-Security-Agent

# Get the latest log file (current session)
LATEST_LOG=$(ls -t logs/security_agent_*.log 2>/dev/null | head -1)

# Show all log lines for this PID - current log only
sudo grep "PID=636393" "$LATEST_LOG" | tail -20

# Or by process name - current log only
sudo grep "Process=groups" "$LATEST_LOG" | tail -20

# Or use the symlink
sudo grep "PID=636393" logs/security_agent.log | tail -20
```

---

### 6. Show a C2 beaconing example from current log (if needed)

```bash
cd ~/Linux-Security-Agent

# Get the latest log file (current session)
LATEST_LOG=$(ls -t logs/security_agent_*.log 2>/dev/null | head -1)

# Show C2 beaconing from current log only
sudo grep -n "C2_BEACONING" "$LATEST_LOG" | tail -10

# Or use the symlink
sudo grep -n "C2_BEACONING" logs/security_agent.log | tail -10
```

This prints lines like:

```text
CONNECTION PATTERN DETECTED: C2_BEACONING PID=... Process=python3
explanation: 'Regular beaconing detected: 2.1s intervals (±3.8s)'
```

---

### 7. Stop everything cleanly (end of demo)

```bash
cd ~/Linux-Security-Agent

sudo pkill -f simple_agent.py
pkill -f app.py
```