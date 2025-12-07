# How to Run the Linux Security Agent

## 🚀 Quick Start Guide

### Prerequisites
- **Linux VM** (Ubuntu 22.04 LTS recommended)
- **Root/sudo access** (required for eBPF)
- **Python 3.8+**
- **Internet connection** (for installing dependencies)

---

## Step 1: Setup on VM

### 1.1 Install System Dependencies

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install eBPF/BCC tools (required)
sudo apt-get install -y bpfcc-tools python3-bpfcc linux-headers-$(uname -r)

# Install Python and Git
sudo apt-get install -y python3-pip git

# Install Docker (optional, for container monitoring)
sudo apt-get install -y docker.io
sudo systemctl start docker
```

### 1.2 Clone and Install Project

```bash
# Clone repository
git clone https://github.com/likitha-shankar/Linux-Security-Agent.git
cd Linux-Security-Agent

# Install Python dependencies (system-wide for sudo use)
sudo pip3 install -r requirements.txt
```

### 1.3 Train ML Models (Required Before Running Agent)

**Option A: Automated Setup (Recommended)**

```bash
# Complete automated setup - downloads ADFA-LD dataset and trains models
bash scripts/complete_training_setup.sh
```

This script will:
1. Download ADFA-LD dataset from GitHub
2. Convert syscall numbers to names
3. Train all ML models with progress indicators
4. Verify models are working

**Option B: Manual Setup**

```bash
# Step 1: Setup ADFA-LD dataset
bash scripts/setup_adfa_ld_dataset.sh

# Step 2: Convert to training format
python3 scripts/download_real_datasets.py --adfa-dir ~/datasets/ADFA-LD/ADFA-LD --output datasets/adfa_training.json

# Step 3: Train models
python3 scripts/train_with_progress.py --file datasets/adfa_training.json
```

**Training Details**:
- **Dataset**: ADFA-LD (5,205 real syscall sequences)
- **Time**: ~5 seconds
- **Models**: Isolation Forest, One-Class SVM, DBSCAN
- **Location**: `~/.cache/security_agent/`

### 1.4 Verify Setup

```bash
# Test eBPF is working
python3 -c "from bcc import BPF; print('✅ eBPF working!')"

# Test imports
python3 -c "from core.simple_agent import SimpleSecurityAgent; print('✅ Agent ready!')"

# Verify models are trained
python3 -c "from core.enhanced_anomaly_detector import EnhancedAnomalyDetector; d = EnhancedAnomalyDetector(); d._load_models(); print('✅ Models loaded!' if d.is_fitted else '❌ Models not found')"
```

---

## Step 2: Run the Agent

### Option A: Simple Agent (Recommended for First Time)

```bash
# Run with eBPF collector (best performance)
sudo python3 core/simple_agent.py --collector ebpf --threshold 20

# Or with auditd collector (more reliable fallback)
sudo python3 core/simple_agent.py --collector auditd --threshold 20

# Run in headless mode (no dashboard, for automation)
sudo python3 core/simple_agent.py --collector ebpf --threshold 20 --headless
```

**What you'll see:**
- Real-time dashboard showing processes, risk scores, and anomalies
- Live syscall monitoring
- Automatic anomaly detection

**To stop:** Press `Ctrl+C`

---

### Option B: Web Dashboard (Recommended for Monitoring)

#### 2.1 Start Web Dashboard

```bash
# Install web dependencies
cd web
pip3 install --user -r requirements.txt

# Start web server
python3 app.py
```

**Dashboard will be available at:**
- From VM: `http://localhost:5001`
- From browser SSH: `http://localhost:5001` (in new tab)
- Public IP: `http://YOUR_VM_IP:5001` (if firewall allows)

#### 2.2 Start Agent Manually

**In a separate terminal (SSH into VM):**

```bash
cd ~/Linux-Security-Agent
sudo python3 core/simple_agent.py --collector ebpf --threshold 20
```

**The dashboard will automatically detect and show logs!**

---

## Step 3: Test with Attacks

### 3.1 Run Attack Simulations

**In a separate terminal (while agent is running):**

```bash
cd ~/Linux-Security-Agent

# Run all attack simulations
python3 scripts/simulate_attacks.py

# Or run specific attack
python3 -c "from scripts.simulate_attacks import simulate_privilege_escalation; simulate_privilege_escalation()"
```

**What to expect:**
- Agent will detect high-risk syscalls
- Dashboard will show alerts
- Logs will show detailed anomaly explanations

---

## Step 4: View Logs

### 4.1 View Agent Logs

```bash
# View live logs
tail -f logs/security_agent.log

# View only anomalies
tail -f logs/security_agent.log | grep "ANOMALY DETECTED"

# View only high-risk detections
tail -f logs/security_agent.log | grep "HIGH RISK"
```

### 4.2 View Enhanced Anomaly Details

```bash
# See detailed anomaly explanations
tail -f logs/security_agent.log | grep -A 15 "ANOMALY DETECTED"
```

---

## Step 5: Automated Testing (Optional)

### 5.1 Run Complete Test Suite

```bash
# Run all tests (pre-flight, unit tests, attacks, reports)
sudo python3 scripts/automate_all_tests.py

# Options:
#   --keep-agent    Keep agent running after tests
#   --no-unit-tests Skip unit tests
```

### 5.2 Run Comprehensive Agent Test

```bash
# Start agent, run attacks, verify detections
sudo python3 scripts/comprehensive_agent_test.py
```

---

## 📋 Common Commands Reference

### Agent Commands

```bash
# Basic run
sudo python3 core/simple_agent.py --collector ebpf --threshold 20

# With different threshold (higher = less sensitive)
sudo python3 core/simple_agent.py --collector ebpf --threshold 30

# Headless mode (no dashboard)
sudo python3 core/simple_agent.py --collector ebpf --threshold 20 --headless

# With config file
sudo python3 core/simple_agent.py --config config/config.yml
```

### Web Dashboard Commands

```bash
# Start dashboard
cd web && python3 app.py

# Start dashboard in background
cd web && nohup python3 app.py > dashboard.log 2>&1 &

# Stop dashboard
pkill -f "app.py"
```

### Testing Commands

```bash
# Run all attacks
python3 scripts/simulate_attacks.py

# Run specific test
python3 scripts/test_anomaly_logging.py

# Measure false positives
python3 scripts/measure_false_positives.py

# Benchmark performance
sudo python3 scripts/benchmark_under_load.py
```

---

## 🔧 Troubleshooting

### Issue: "No module named 'bcc'"
**Solution:**
```bash
sudo apt-get install -y bpfcc-tools python3-bpfcc
```

### Issue: "Permission denied" for eBPF
**Solution:**
```bash
# Must run with sudo
sudo python3 core/simple_agent.py --collector ebpf
```

### Issue: "No events captured"
**Solution:**
- Wait 10-20 seconds for events to start
- Check if eBPF is working: `python3 -c "from bcc import BPF; print('OK')"`
- Try auditd collector: `--collector auditd`

### Issue: Dashboard shows "Agent Stopped" but agent is running
**Solution:**
- Refresh the browser page
- Check if log file exists: `ls -la logs/security_agent.log`
- Restart dashboard: `pkill -f app.py && cd web && python3 app.py`

### Issue: Too many false positives
**Solution:**
- Increase threshold: `--threshold 30` or `--threshold 40`
- Check excluded processes in `core/simple_agent.py`
- Review logs to see what's being flagged

---

## 📊 What to Expect

### Normal Operation

- **Dashboard shows:** Processes with risk scores (0-100) and anomaly scores (0-100)
- **Logs show:** Periodic score updates, occasional anomalies
- **Performance:** ~50MB memory, <5% CPU

### During Attacks

- **Dashboard shows:** High-risk alerts, anomaly warnings
- **Logs show:** Detailed explanations of what's anomalous
- **Alerts:** Visual indicators in dashboard

### Score Interpretation

- **Risk Score 0-30:** Normal
- **Risk Score 30-50:** Suspicious
- **Risk Score 50+:** High Risk

- **Anomaly Score 0-10:** Normal
- **Anomaly Score 10-30:** Unusual
- **Anomaly Score 30+:** Anomalous

---

## 🎯 Quick Test Workflow

1. **Start agent:**
   ```bash
   sudo python3 core/simple_agent.py --collector ebpf --threshold 20
   ```

2. **In another terminal, run attack:**
   ```bash
   python3 scripts/simulate_attacks.py
   ```

3. **Watch dashboard for alerts** or check logs:
   ```bash
   tail -f logs/security_agent.log | grep -A 10 "HIGH RISK"
   ```

4. **Stop agent:** Press `Ctrl+C`

---

## 📝 Notes

- **First run:** May take 10-20 seconds to start capturing events
- **ML models:** Will train automatically on first run (takes ~30 seconds)
- **Logs:** Saved to `logs/security_agent.log` (rotates at 10MB)
- **Performance:** Best on dedicated VM with 2+ CPU cores

---

## 🆘 Need Help?

- Check logs: `tail -f logs/security_agent.log`
- Review documentation: `docs/CLOUD_DEPLOYMENT.md`
- Check project status: `docs/PROJECT_STATUS.md`

