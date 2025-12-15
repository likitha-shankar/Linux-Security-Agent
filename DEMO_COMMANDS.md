# Demo Commands - Quick Reference
**Quick reference for all demo commands**

---

## 🚀 Quick Start (One Command)

```bash
# On VM - Start everything automatically
cd ~/Linux-Security-Agent
bash START_COMPLETE_DEMO.sh
```

---

## 📋 Step-by-Step Commands

### 1. Configure Auditd Rules

```bash
# Clear existing rules
sudo auditctl -D

# Add network syscall monitoring rules
sudo auditctl -a always,exit -F arch=b64 -S socket -S connect -S bind -S accept -S sendto -S recvfrom -k network_syscalls

# Verify rules
sudo auditctl -l | grep network_syscalls
```

### 2. Start Security Agent

```bash
cd ~/Linux-Security-Agent

# Start agent in headless mode
sudo python3 core/simple_agent.py --collector auditd --threshold 20 --headless

# Or start in background
sudo nohup python3 core/simple_agent.py --collector auditd --threshold 20 --headless >/tmp/agent.log 2>&1 &
```

### 3. Start Web Dashboard

```bash
cd ~/Linux-Security-Agent/web

# Start dashboard
python3 app.py

# Or start in background
nohup python3 app.py >/tmp/dashboard.log 2>&1 &

# Access at: http://<VM_IP>:5001
```

### 4. Check Status

```bash
# Check if agent is running
ps aux | grep simple_agent

# Check if dashboard is running
ps aux | grep app.py

# Check dashboard API
curl http://localhost:5001/api/status

# Check agent state
curl http://localhost:5001/api/agent/state | python3 -m json.tool
```

---

## 🎯 Demo Attack Commands

### Port Scan Attack

```bash
# Quick port scan (10 ports)
for i in {8000..8010}; do timeout 0.3 nc -zv localhost $i 2>&1 >/dev/null; done

# More comprehensive port scan (20 ports)
for i in {9000..9020}; do timeout 0.3 nc -zv localhost $i 2>&1 >/dev/null; done

# Using nmap (if available)
nmap -p 8000-8020 localhost
```

### High-Risk Commands

```bash
# Privilege escalation attempt
sudo -n true 2>/dev/null || echo "Privilege check"

# Suspicious file operations
chmod 777 /tmp/test_file
chown root:root /tmp/test_file

# Process manipulation
ptrace -p $(pgrep -n python3) 2>/dev/null || echo "Ptrace attempt"
```

### Run Full Attack Simulation

```bash
cd ~/Linux-Security-Agent

# Run all attack types
python3 scripts/simulate_attacks.py

# This includes:
# - Privilege escalation
# - High-frequency attacks
# - Suspicious file patterns
# - Process churn
# - Network scanning
# - C2 beaconing
# - Ptrace attempts
```

---

## 📊 Monitoring Commands

### View Logs

```bash
# Find latest log file
ls -t logs/security_agent_*.log | head -1

# View last 50 lines
tail -50 logs/security_agent_*.log

# Monitor in real-time
tail -f logs/security_agent_*.log

# Filter for specific events
tail -f logs/security_agent_*.log | grep -E "PORT_SCANNING|HIGH RISK|ANOMALY"
```

### Check Detections

```bash
# Get latest log
LOG=$(ls -t logs/security_agent_*.log | head -1)

# Count detections
echo "Port Scans: $(grep -c PORT_SCANNING "$LOG" 2>/dev/null || echo 0)"
echo "High-Risk: $(grep -c 'HIGH RISK DETECTED' "$LOG" 2>/dev/null || echo 0)"
echo "Anomalies: $(grep -c 'ANOMALY DETECTED\|🤖 ANOMALY' "$LOG" 2>/dev/null || echo 0)"
echo "ML Detections: $(grep -c 'ML RESULT.*IsAnomaly=True' "$LOG" 2>/dev/null || echo 0)"
echo "Total Syscalls: $(grep -c 'syscall' "$LOG" 2>/dev/null || echo 0)"

# Show recent detections
grep -E 'PORT_SCANNING|HIGH RISK|ANOMALY DETECTED' "$LOG" 2>/dev/null | tail -10
```

### Check Dashboard Metrics

```bash
# Get current stats
curl -s http://localhost:5001/api/agent/state | python3 -c '
import sys, json
d = json.load(sys.stdin)
stats = d.get("stats", {})
print(f"Processes: {stats.get(\"processes\", 0)}")
print(f"High Risk: {stats.get(\"high_risk\", 0)}")
print(f"Anomalies: {stats.get(\"anomalies\", 0)}")
print(f"Port Scans: {stats.get(\"port_scans\", 0)}")
print(f"Total Syscalls: {stats.get(\"total_syscalls\", 0)}")
'
```

---

## 🔧 Troubleshooting Commands

### Restart Agent

```bash
# Stop agent
sudo pkill -9 -f simple_agent.py

# Wait a moment
sleep 2

# Restart
sudo python3 core/simple_agent.py --collector auditd --threshold 20 --headless
```

### Restart Dashboard

```bash
# Stop dashboard
pkill -f app.py

# Wait a moment
sleep 2

# Restart
cd ~/Linux-Security-Agent/web
python3 app.py
```

### Check Agent Logs

```bash
# If agent started with nohup
tail -f /tmp/agent.log

# Check for errors
grep -i error /tmp/agent.log | tail -10
```

### Check Dashboard Logs

```bash
# If dashboard started with nohup
tail -f /tmp/dashboard.log

# Check for errors
grep -i error /tmp/dashboard.log | tail -10
```

### Verify Models

```bash
# Check if models are trained
ls -lh ~/.cache/security_agent/*.pkl

# Should show:
# - isolation_forest.pkl
# - one_class_svm.pkl
# - pca.pkl
# - scaler.pkl
```

### Train Models (if needed)

```bash
cd ~/Linux-Security-Agent

# Train with ADFA dataset
python3 scripts/train_with_dataset.py --file datasets/adfa_training.json
```

---

## 🎬 Complete Demo Flow

### Pre-Demo Setup (5 minutes before)

```bash
# 1. SSH to VM
ssh -i ~/.ssh/your_key user@vm_ip

# 2. Navigate to project
cd ~/Linux-Security-Agent

# 3. Start everything
bash START_COMPLETE_DEMO.sh

# 4. Wait 30 seconds for initialization
sleep 30

# 5. Verify everything is running
ps aux | grep -E 'simple_agent|app.py'
curl http://localhost:5001/api/status
```

### During Demo

```bash
# 1. Show normal monitoring (wait 30 seconds)
# Dashboard should show processes and syscalls

# 2. Run port scan attack
for i in {8000..8020}; do timeout 0.3 nc -zv localhost $i 2>&1 >/dev/null; done

# 3. Wait 10 seconds for detection
sleep 10

# 4. Show detection in dashboard/logs
tail -20 logs/security_agent_*.log | grep PORT_SCANNING

# 5. Run full attack simulation
python3 scripts/simulate_attacks.py

# 6. Show all detections
LOG=$(ls -t logs/security_agent_*.log | head -1)
echo "Port Scans: $(grep -c PORT_SCANNING "$LOG")"
echo "High-Risk: $(grep -c 'HIGH RISK DETECTED' "$LOG")"
echo "Anomalies: $(grep -c 'ANOMALY DETECTED' "$LOG")"
```

---

## 📱 Dashboard Access

### Local Access (on VM)

```bash
# Open in browser
http://localhost:5001
```

### Remote Access

```bash
# Option 1: Direct access (if firewall allows)
http://<VM_IP>:5001

# Option 2: SSH tunnel
ssh -L 5001:localhost:5001 user@vm_ip

# Then access locally
http://localhost:5001
```

---

## 🛑 Stop Everything

```bash
# Stop agent
sudo pkill -9 -f simple_agent.py

# Stop dashboard
pkill -f app.py

# Verify stopped
ps aux | grep -E 'simple_agent|app.py'
```

---

## 📝 Quick Reference Card

```bash
# START
bash START_COMPLETE_DEMO.sh

# ATTACK
python3 scripts/simulate_attacks.py

# CHECK
curl http://localhost:5001/api/status

# LOGS
tail -f logs/security_agent_*.log | grep -E "PORT_SCANNING|HIGH RISK|ANOMALY"

# STOP
sudo pkill -9 -f simple_agent.py && pkill -f app.py
```

---

## 🎯 Key Metrics to Show

```bash
# Get all metrics at once
LOG=$(ls -t logs/security_agent_*.log | head -1)
echo "=== DETECTION METRICS ==="
echo "Port Scans: $(grep -c PORT_SCANNING "$LOG" 2>/dev/null || echo 0)"
echo "High-Risk: $(grep -c 'HIGH RISK DETECTED' "$LOG" 2>/dev/null || echo 0)"
echo "Anomalies: $(grep -c 'ANOMALY DETECTED\|🤖 ANOMALY' "$LOG" 2>/dev/null || echo 0)"
echo "ML Detections: $(grep -c 'ML RESULT.*IsAnomaly=True' "$LOG" 2>/dev/null || echo 0)"
echo "Total Syscalls: $(grep -c 'syscall' "$LOG" 2>/dev/null || echo 0)"
```

---

**Last Updated:** December 11, 2025
