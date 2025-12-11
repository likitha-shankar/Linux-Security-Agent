# Linux Security Agent - Demo Guide

This guide provides commands and expected outputs to help you demonstrate the Linux Security Agent effectively.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Starting the Agent](#starting-the-agent)
3. [Starting the Web Dashboard](#starting-the-web-dashboard)
4. [Verification Commands](#verification-commands)
5. [Demo Scenarios](#demo-scenarios)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Check Python and Dependencies
```bash
# Check Python version (should be 3.8+)
python3 --version
# Expected: Python 3.x.x

# Check if required packages are installed
pip3 list | grep -E "flask|psutil|bcc|rich"
# Expected: flask, psutil, bcc-python, rich should be listed
```

### Check eBPF Support
```bash
# Check if eBPF is available (requires root or capabilities)
sudo python3 -c "from bcc import BPF; print('✅ eBPF available')"
# Expected: ✅ eBPF available
# If error: eBPF not available, may need to install bcc-tools
```

### Verify Agent Files
```bash
# Check if agent files exist
ls -la core/simple_agent.py web/app.py
# Expected: Both files should exist
```

---

## Starting the Agent

### Option 1: Start Agent Directly (Terminal Dashboard)
```bash
# Navigate to project directory
cd /path/to/linux_security_agent

# Start the agent (requires sudo for eBPF)
sudo python3 core/simple_agent.py
```

**Expected Output:**
- Terminal dashboard appears with:
  - Stats panel showing: Processes, High Risk, Anomalies, Attacks, Syscalls
  - Process list with real-time updates
  - Live syscall monitoring
- Logs show: `🔄 Resetting agent state for new run...`
- Dashboard updates every 2 seconds
- Process names should resolve (not `pid_XXXXX`)

**To Stop:** Press `Ctrl+C`

---

### Option 2: Start Agent via Web Dashboard
```bash
# First, start the web dashboard (see below)
# Then click "Start Agent" button in the web UI
```

**Expected Behavior:**
- Agent status changes from "Agent Stopped" to "Agent Running"
- Dashboard automatically resets and starts fresh
- Terminal dashboard appears in the background
- Stats begin updating in real-time

---

## Starting the Web Dashboard

### Start Web Dashboard
```bash
# Navigate to project directory
cd /path/to/linux_security_agent

# Start Flask web server
python3 web/app.py
```

**Expected Output:**
```
 * Running on http://0.0.0.0:5001
 * Running on http://127.0.0.1:5001
```

**Access Dashboard:**
- Local: `http://localhost:5001`
- Remote: `http://<VM_IP>:5001`
- SSH Tunnel: `ssh -L 5001:localhost:5001 user@vm_ip` then `http://localhost:5001`

**Expected Dashboard Features:**
- Header with agent status indicator
- 6 metric cards: Processes, High Risk, Anomalies, Attacks, Total Syscalls
- Activity Timeline chart (line graph)
- Recent High-Risk section
- Recent Attacks section
- Process list with details
- Live log terminal

**To Stop:** Press `Ctrl+C`

---

## Verification Commands

### Check Agent Status
```bash
# Check if agent process is running
ps aux | grep simple_agent.py | grep -v grep
# Expected: Shows python3 process running simple_agent.py

# Check agent PID
pgrep -f simple_agent.py
# Expected: Returns a PID number
```

### Check Web Dashboard Status
```bash
# Check if Flask app is running
ps aux | grep app.py | grep -v grep
# Expected: Shows python3 process running app.py

# Check if port 5001 is listening
netstat -tuln | grep 5001
# OR
ss -tuln | grep 5001
# Expected: Shows LISTEN on port 5001
```

### Check Agent State File
```bash
# Check if state file exists and is being updated
ls -lh /tmp/security_agent_state.json
# Expected: File exists and has recent modification time

# View state file contents
cat /tmp/security_agent_state.json | python3 -m json.tool | head -20
# Expected: JSON with stats and processes
```

### Check Agent Logs
```bash
# Find log file location
ls -lh logs/*.log | tail -1
# Expected: Most recent log file

# View last 20 lines of log
tail -20 logs/security_agent_*.log
# Expected: Recent log entries with timestamps

# Monitor logs in real-time
tail -f logs/security_agent_*.log
# Expected: Live log stream
```

### Check eBPF Syscall Capture
```bash
# Verify eBPF is capturing syscalls (run while agent is running)
# Look for syscall entries in logs
grep -i "syscall" logs/security_agent_*.log | tail -10
# Expected: Shows syscall events with PIDs and process names
```

---

## Demo Scenarios

### Scenario 1: Basic Monitoring Demo

**Steps:**
1. Start web dashboard: `python3 web/app.py`
2. Open browser: `http://localhost:5001`
3. Click "Start Agent" button
4. Wait 10-15 seconds

**Expected Results:**
- Agent status: "Agent Running" (green dot)
- Stats cards show increasing numbers:
  - Processes: 5-20+
  - Syscalls: Increasing rapidly
  - High Risk: May show 0-5
  - Anomalies: May show 0-10
- Activity Timeline chart shows data points
- Process list populates with running processes
- Log terminal shows live events

**What to Say:**
> "The agent is now monitoring all system calls in real-time using eBPF. You can see processes being tracked, their risk scores, and any anomalies detected."

---

### Scenario 2: Attack Detection Demo

#### Option A: Using Attack Simulation Script (Recommended)

**Steps:**
1. Start agent (via web or terminal)
2. Wait for baseline activity (30 seconds)
3. In a separate terminal, run the attack simulation script:
   ```bash
   # Run all attack simulations
   python3 scripts/simulate_attacks.py
   ```

**Available Attacks in the Script:**
- **Privilege Escalation**: Attempts to gain elevated privileges
- **High-Frequency Attack**: Rapid syscall patterns
- **Suspicious File Patterns**: Unusual file operations
- **Process Churn**: Rapid process creation/termination
- **Network Scanning**: Port scanning patterns
- **Ptrace Attempts**: Process debugging/tracing attempts

**Expected Results:**
- Attack count increases in dashboard
- "Recent Attacks" section shows detections
- High-risk processes appear with elevated risk scores (50-100)
- Logs show detailed attack alerts
- ML anomaly detection flags suspicious patterns
- Dashboard stats update in real-time

**What to Say:**
> "The agent detected multiple attack patterns - notice how the attack counter increased, risk scores spiked to 50-100, and the system flagged these as potential threats. The ML-based anomaly detection is identifying these patterns in real-time."

#### Option B: Manual Attack Commands

**Steps:**
1. Start agent (via web or terminal)
2. Wait for baseline activity (30 seconds)
3. Run manual attack commands:
   ```bash
   # Simulate port scanning
   for i in {1..50}; do nc -zv localhost $((8000+i)) 2>&1 | head -1; done
   
   # OR simulate file tampering
   sudo touch /tmp/suspicious_file
   sudo chmod 777 /tmp/suspicious_file
   
   # OR simulate privilege escalation attempt
   sudo -n true 2>/dev/null || echo "Privilege check"
   ```

**Expected Results:**
- Attack count increases
- "Recent Attacks" section shows detection
- High-risk processes may appear
- Logs show attack alerts

**What to Say:**
> "The agent detected suspicious activity - notice how the attack counter increased and the system flagged this as a potential threat."

---

### Scenario 3: Dashboard Reset Demo

**Steps:**
1. Let agent run for 1-2 minutes (collect data)
2. Stop agent (Ctrl+C or "Stop Agent" button)
3. Wait 5 seconds
4. Start agent again

**Expected Results:**
- Chart freezes when agent stops (no new data points)
- When restarted:
  - All stats reset to 0
  - Chart clears and starts fresh
  - Process list clears
  - Log shows: "🔄 Dashboard values reset - starting fresh monitoring session"

**What to Say:**
> "Notice how the dashboard automatically resets when the agent restarts, ensuring we're always looking at fresh data from the current monitoring session."

---

### Scenario 4: Real-Time Updates Demo

**Steps:**
1. Start agent and dashboard
2. Open two browser windows side-by-side:
   - Window 1: Web dashboard
   - Window 2: Terminal with `tail -f logs/security_agent_*.log`

**Expected Results:**
- Web dashboard updates every 2 seconds
- Terminal logs show same events in real-time
- Both show synchronized data

**What to Say:**
> "The web dashboard and terminal dashboard are synchronized - they both read from the same agent state, ensuring consistency across interfaces."

---

### Scenario 5: Process Name Resolution Demo

**Steps:**
1. Start agent
2. Run a quick command: `ls -la /tmp`
3. Check process list

**Expected Results:**
- Process shows as "ls" or similar (not `pid_XXXXX`)
- Recent syscalls shown for the process
- Risk and anomaly scores displayed

**What to Say:**
> "The agent uses multiple methods to resolve process names - from kernel data, /proc filesystem, and process utilities - ensuring accurate identification even for short-lived processes."

---

## Troubleshooting

### Agent Won't Start
```bash
# Check for errors
sudo python3 core/simple_agent.py 2>&1 | head -20
# Expected: Should show dashboard, not errors

# Check eBPF availability
sudo python3 -c "from bcc import BPF; print('OK')"
# If error: Install bcc-tools: sudo apt-get install bpfcc-tools python3-bpfcc
```

### Web Dashboard Not Accessible
```bash
# Check if Flask is running
ps aux | grep app.py

# Check firewall
sudo ufw status
# If needed: sudo ufw allow 5001

# Check if port is listening
ss -tuln | grep 5001
```

### Chart Not Updating
```bash
# Hard refresh browser: Ctrl+F5 (Windows/Linux) or Cmd+Shift+R (Mac)
# Check browser console for errors (F12)
# Verify agent is running: Check /api/status endpoint
```

### Process Names Show as pid_XXXXX
```bash
# This is normal for very short-lived processes
# Check logs to see if names resolve over time
tail -f logs/security_agent_*.log | grep -i "process="
# Expected: Should see real names for longer-running processes
```

### State File Not Found
```bash
# Check permissions
ls -la /tmp/security_agent_state.json
# Expected: Should be readable (644 permissions)

# Check if agent is writing state
sudo strace -p $(pgrep -f simple_agent.py) 2>&1 | grep state
# Expected: Shows file write operations
```

---

## Quick Reference Commands

```bash
# Start agent (terminal)
sudo python3 core/simple_agent.py

# Start web dashboard
python3 web/app.py

# Run attack simulations
python3 scripts/simulate_attacks.py

# Run specific attack (example: privilege escalation)
python3 -c "from scripts.simulate_attacks import simulate_privilege_escalation; simulate_privilege_escalation()"

# Check agent status
curl http://localhost:5001/api/status

# Check agent state
curl http://localhost:5001/api/agent/state | python3 -m json.tool

# View recent logs
tail -50 logs/security_agent_*.log

# Monitor logs live
tail -f logs/security_agent_*.log

# View only attack detections
tail -f logs/security_agent_*.log | grep -i "attack\|port.*scan\|c2\|beacon"

# View only high-risk processes
tail -f logs/security_agent_*.log | grep -i "high risk"

# Stop agent
sudo pkill -f simple_agent.py

# Stop web dashboard
pkill -f app.py
```

---

## Attack Simulation Commands

### Run All Attacks
```bash
# Run complete attack simulation suite
python3 scripts/simulate_attacks.py
```

**What This Does:**
- Runs 6 different attack patterns sequentially
- Each attack is safe and non-destructive
- Designed to trigger agent detection mechanisms
- Takes approximately 2-3 minutes to complete

**Expected Output:**
```
🔴 SAFE ATTACK SIMULATION - Testing Security Agent
⚠️  WARNING: This script simulates attack patterns
⚠️  Only run in a VM or isolated environment
⚠️  All operations are safe and non-destructive

Press Enter to start attack simulation...

🔴 Attack: Privilege Escalation
   Description: Attempts to gain elevated privileges...
✅ Privilege escalation pattern simulated

🔴 Attack: High-Frequency Attack
   Description: Rapid syscall patterns...
✅ High-frequency pattern simulated

... (continues for all 6 attacks)

✅ Attack Simulation Complete
Check your security agent dashboard for detection results!
```

### Run Individual Attacks
```bash
# Privilege escalation
python3 -c "from scripts.simulate_attacks import simulate_privilege_escalation; simulate_privilege_escalation()"

# High-frequency attack
python3 -c "from scripts.simulate_attacks import simulate_high_frequency_attack; simulate_high_frequency_attack()"

# Suspicious file patterns
python3 -c "from scripts.simulate_attacks import simulate_suspicious_file_patterns; simulate_suspicious_file_patterns()"

# Process churn
python3 -c "from scripts.simulate_attacks import simulate_process_churn; simulate_process_churn()"

# Network scanning
python3 -c "from scripts.simulate_attacks import simulate_network_scanning; simulate_network_scanning()"

# Ptrace attempts
python3 -c "from scripts.simulate_attacks import simulate_ptrace_attempts; simulate_ptrace_attempts()"
```

### Verify Attack Detection
```bash
# Check logs for attack detections
tail -100 logs/security_agent_*.log | grep -i "attack\|port.*scan\|c2\|beacon"

# Check for high-risk processes
tail -100 logs/security_agent_*.log | grep -i "high risk"

# Monitor in real-time during attack
tail -f logs/security_agent_*.log | grep -E "ATTACK|HIGH RISK|ANOMALY"
```

**Expected Detection Indicators:**
- Log entries with "ATTACK DETECTED" or "PORT SCAN" or "C2 BEACON"
- Risk scores spiking to 50-100
- High-risk processes appearing in dashboard
- Attack counter increasing in stats
- ML anomaly detection flags

---

## Expected Performance Metrics

**Normal Operation:**
- Syscall capture rate: 100-1000+ syscalls/second (depends on system activity)
- Dashboard update frequency: Every 2 seconds
- Process name resolution: 90%+ success rate
- Memory usage: 50-200 MB (agent + dashboard)
- CPU usage: 1-5% (depends on syscall volume)

**Attack Detection:**
- Port scanning: Detected within 10-30 seconds
- C2 beaconing: Detected within 30-60 seconds
- File tampering: Detected immediately
- Privilege escalation: Detected within 5-15 seconds
- High-frequency attacks: Detected within 5-10 seconds
- Process churn: Detected within 10-20 seconds

---

## Demo Tips

1. **Start Fresh**: Always restart the agent before a demo to show clean state
2. **Show Both Views**: Demonstrate both terminal and web dashboards
3. **Generate Activity**: Run some commands during demo to show real-time updates
4. **Explain eBPF**: Mention that this uses real kernel-level monitoring, not simulation
5. **Highlight Accuracy**: Show that process names and syscalls are real, not synthetic
6. **Show Reset**: Demonstrate the automatic reset feature
7. **Check Logs**: Show the detailed logs to prove real monitoring

---

## Notes

- Agent requires `sudo` for eBPF access
- Web dashboard runs on port 5001 (configurable in `web/app.py`)
- State file location: `/tmp/security_agent_state.json`
- Log files: `logs/security_agent_YYYYMMDD_HHMMSS.log`
- Chart only updates when agent is running (freezes when stopped)
- Dashboard automatically resets when agent restarts

---

## Current Status (December 2025)

### ✅ Working Features
- **Normal Monitoring**: ✅ Working (real syscalls captured)
- **Port Scanning Detection**: ✅ Fixed and working (requires 5+ unique ports)
- **C2 Beaconing Detection**: ✅ Fixed and working (requires 3+ connections to same port with regular intervals)
- **High Risk Detection**: ✅ Working
- **State File Updates**: ✅ Working (updates every 2 seconds)
- **Web Dashboard**: ✅ Working

### ⚠️ Requirements
- **Auditd Configuration**: Must configure auditd rules for network syscalls:
  ```bash
  sudo auditctl -a always,exit -F arch=b64 -S socket -S connect -S bind -S accept -S sendto -S recvfrom -k network_syscalls
  ```

### 📊 Test Results
- **Black Box Test Score**: 5/5 (100%)
- **Port Scanning**: ✅ Detected (22+ scans in tests)
- **C2 Beaconing**: ✅ Detected (1+ beacons in tests)
- **Data Authenticity**: ✅ Confirmed REAL (not simulated)

**Last Updated:** December 2025 - All fixes applied and verified (Black box testing: November 2025)
**Version:** 2.0

