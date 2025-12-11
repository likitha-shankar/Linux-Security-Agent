# Professor Questions: Attack Testing & Evaluation

## Overview
This document anticipates likely questions a professor might ask regarding attack testing, detection capabilities, and evaluation of the Linux Security Agent project.

---

## 1. Attack Coverage & MITRE ATT&CK Framework

### Likely Questions:
- **"Which MITRE ATT&CK techniques can you detect?"**
  - **Answer:** Currently detecting T1046 (Network Service Scanning), T1068 (Privilege Escalation), T1071 (Application Layer Protocol - limited), T1055 (Process Injection - partial)

- **"Can you demonstrate T1046 (Network Service Scanning)?"**
  - **Answer:** ✅ Yes - 72 port scans detected in 10-minute test
  - **Demo:** Run `nmap` or rapid socket connections, show detection in dashboard

- **"Can you detect T1071 (Application Layer Protocol) for C2 beaconing?"**
  - **Answer:** ⚠️ Limited - C2 detection needs improvement (0 detections in test)
  - **Status:** Connection pattern analyzer exists but needs tuning

- **"What about privilege escalation (T1068)?"**
  - **Answer:** ✅ Yes - High-risk detection works (52 detections in test)
  - **Demo:** Show setuid/setgid patterns being flagged

---

## 2. Real Attack Scenarios

### Likely Questions:
- **"Can you detect a real port scan using `nmap`?"**
  - **Answer:** ✅ Should work - Test with actual `nmap` command
  - **Demo Command:** `nmap -p 1-1000 localhost`
  - **Expected:** Port scanning detection triggered

- **"What about a reverse shell connection?"**
  - **Answer:** ⚠️ May need explicit testing
  - **Status:** Network connections tracked, but reverse shell pattern needs validation

- **"Can you catch a process injection attack?"**
  - **Answer:** ⚠️ Partial - Ptrace/setuid patterns detected
  - **Status:** High-risk syscalls flagged, but full injection chain may need refinement

- **"What if someone uses `curl` to exfiltrate data?"**
  - **Answer:** ⚠️ May appear as normal network activity
  - **Limitation:** Legitimate tools can bypass detection if not flagged as high-risk

---

## 3. ML & Anomaly Detection

### Likely Questions:
- **"How does your ML model perform? What's the accuracy?"**
  - **Answer:** ⚠️ Needs formal metrics (precision, recall, F1)
  - **Status:** ML models running but formal evaluation needed
  - **Current:** Isolation Forest, One-Class SVM, DBSCAN ensemble

- **"What's your false positive rate?"**
  - **Answer:** ⚠️ Not measured yet
  - **Action Needed:** Run false positive analysis with normal traffic

- **"Can you show me training data and validation results?"**
  - **Answer:** ⚠️ Needs documented training/validation
  - **Available:** Training datasets exist (`adfa_training.json`, `realistic_training_data.json`)
  - **Missing:** Validation metrics and test results

- **"How does it handle concept drift?"**
  - **Answer:** ⚠️ Incremental training exists but needs evaluation
  - **Feature:** `incremental_trainer.py` available
  - **Status:** Not fully tested in production

---

## 4. Performance & Scalability

### Likely Questions:
- **"How many events per second can you process?"**
  - **Answer:** ⚠️ Needs benchmarking
  - **Current:** ~994 events in 10 minutes (~1.66 events/sec average)
  - **Action Needed:** Stress test with high-volume syscalls

- **"What's the overhead on system performance?"**
  - **Answer:** ✅ Low overhead observed
  - **Current:** ~3% CPU usage, ~4.8% memory (192MB)
  - **Status:** Good performance, but needs formal load testing

- **"Can it handle a DDoS-like burst of syscalls?"**
  - **Answer:** ⚠️ Needs stress testing
  - **Action Needed:** Simulate burst of 1000+ syscalls/second

---

## 5. Comparison & Baselines

### Likely Questions:
- **"How does this compare to OSSEC or Wazuh?"**
  - **Answer:** ⚠️ Needs comparison
  - **Our Advantages:**
    - Real-time syscall-level monitoring
    - ML-based anomaly detection
    - Lightweight eBPF/auditd approach
  - **Their Advantages:**
    - Mature, production-ready
    - Extensive rule sets
    - Better integration options

- **"What's your detection rate vs. signature-based tools?"**
  - **Answer:** ⚠️ Needs metrics
  - **Approach:** Hybrid (rules + ML) vs. pure signature-based
  - **Benefit:** Can detect unknown attacks via ML

- **"Why use ML instead of just rules?"**
  - **Answer:** 
    - ML detects unknown/zero-day attacks
    - Adapts to new patterns
    - Complements rule-based detection
    - Handles polymorphic attacks

---

## 6. Edge Cases & Evasion

### Likely Questions:
- **"What if an attacker uses legitimate tools (like `curl`, `wget`)?"**
  - **Answer:** ⚠️ May bypass detection
  - **Limitation:** Legitimate tools can be used maliciously
  - **Mitigation:** Context-aware detection (frequency, patterns, destinations)

- **"Can you detect slow, low-volume attacks?"**
  - **Answer:** ⚠️ C2 beaconing needs improvement
  - **Status:** Connection pattern analyzer exists but needs tuning
  - **Challenge:** Low-volume attacks harder to detect

- **"What about encrypted traffic?"**
  - **Answer:** ⚠️ Limited visibility (syscall-level only)
  - **Approach:** Detect at syscall level, not packet level
  - **Benefit:** Works regardless of encryption
  - **Limitation:** Can't inspect payload content

- **"Can attackers evade by using Python scripts?"**
  - **Answer:** ⚠️ Currently excluded; may need adjustment
  - **Status:** Python processes excluded from some checks
  - **Trade-off:** Reduces false positives but may miss Python-based attacks

---

## 7. Practical Demonstration

### Likely Questions:
- **"Show me a live attack being detected"**
  - **Answer:** ✅ Can demo port scans and high-risk processes
  - **Demo Script:**
    1. Start agent
    2. Run `nmap -p 1-100 localhost`
    3. Show detection in dashboard/logs
    4. Run high-risk command (e.g., `chmod 777 /tmp/test`)
    5. Show high-risk alert

- **"Can you show the alert in real-time on the dashboard?"**
  - **Answer:** ✅ Yes - Dashboard works
  - **Demo:** Show dashboard updating with live detections
  - **Features:** Real-time updates, process tracking, risk scores

- **"What happens when you detect an attack? Do you block it?"**
  - **Answer:** ⚠️ Currently logs only; no automated response
  - **Current:** Logging and alerting
  - **Future:** Could add automated response (kill process, block IP, etc.)

---

## 8. Limitations & Honesty

### Likely Questions:
- **"What are the main limitations?"**
  - **Answer:** Be honest:
    - ✅ Port scanning works (72 detections)
    - ⚠️ C2 beaconing needs improvement (0 detections)
    - ⚠️ ML anomalies need more training data
    - ⚠️ No automated response/blocking
    - ⚠️ Limited to syscall-level visibility
    - ⚠️ Python processes excluded (may miss Python-based attacks)

- **"What would you improve next?"**
  - **Answer:**
    1. Fix C2 beaconing detection
    2. Improve ML training with more diverse data
    3. Add automated response capabilities
    4. Formal performance benchmarking
    5. Reduce false positives
    6. Better process tracking for short-lived processes

---

## What to Prepare for Demo

### 1. Live Demo Script:
```bash
# 1. Start agent
sudo python3 core/simple_agent.py --collector auditd --threshold 20 --headless

# 2. Run port scan
nmap -p 1-100 localhost

# 3. Run high-risk command
chmod 777 /tmp/test_file

# 4. Show dashboard
# Open http://VM_IP:5001

# 5. Show logs
tail -f logs/security_agent_*.log | grep -E "PORT_SCANNING|HIGH RISK"
```

### 2. Metrics to Have Ready:
- **Detection Rates:**
  - Port Scans: 72 detections (10-min test)
  - High-Risk: 52 detections (10-min test)
  - C2 Beacons: 0 (needs improvement)
  - Anomalies: 0 (needs more training)

- **Performance:**
  - CPU: ~3% overhead
  - Memory: ~192MB
  - Events/sec: ~1.66 avg (needs stress test)

- **False Positive Rate:**
  - ⚠️ Not measured yet

### 3. Honest Limitations:
- ✅ **What Works:**
  - Port scanning detection
  - High-risk process detection
  - Real-time monitoring
  - Dashboard visualization
  - Syscall capture

- ⚠️ **What Needs Work:**
  - C2 beaconing detection
  - ML anomaly detection (needs more training)
  - Automated response
  - Performance benchmarking
  - False positive analysis

### 4. Architecture Explanation:
- **Why eBPF + auditd:**
  - Kernel-level visibility
  - Low overhead
  - Works without modifying applications
  - Cross-application monitoring

- **How ML complements rules:**
  - Rules catch known patterns
  - ML catches unknown/zero-day attacks
  - Ensemble approach for robustness

- **How connection pattern analysis works:**
  - Tracks connections per process
  - Detects rapid port variation (scanning)
  - Detects regular intervals (beaconing)
  - ⚠️ Currently limited by port availability from auditd

---

## Key Talking Points

### Strengths:
1. **Real-time monitoring** - Live syscall capture
2. **Hybrid approach** - Rules + ML for comprehensive detection
3. **Low overhead** - ~3% CPU, minimal impact
4. **Dashboard** - Real-time visualization
5. **Port scanning detection** - Proven to work (72 detections)

### Areas for Improvement:
1. **C2 beaconing** - Needs tuning
2. **ML training** - Needs more diverse data
3. **Automated response** - Currently logging only
4. **Performance testing** - Needs formal benchmarks
5. **False positive analysis** - Needs measurement

### Research Contributions:
1. **Hybrid detection** - Combining rules and ML
2. **Syscall-level analysis** - Works regardless of encryption
3. **Real-time processing** - Low-latency detection
4. **Connection pattern analysis** - Detecting network attacks

---

## Bottom Line

**Focus on what works:**
- Port scanning detection ✅
- High-risk process detection ✅
- Real-time monitoring ✅
- Dashboard ✅

**Be honest about limitations:**
- C2 detection needs work ⚠️
- ML needs more training data ⚠️
- No automated response ⚠️

**Emphasize:**
- Real-time capabilities
- Low overhead
- Hybrid approach (rules + ML)
- Syscall-level visibility (works with encryption)

**Be ready to discuss:**
- Trade-offs and design decisions
- Future improvements
- Comparison with existing tools
- Research contributions

---

## Test Results Summary (10-Minute Test)

- **Duration:** ~10 minutes
- **Port Scans Detected:** 72
- **High-Risk Processes:** 52
- **Total Syscalls Captured:** 994
- **C2 Beacons:** 0 (needs improvement)
- **ML Anomalies:** 0 (needs more training)
- **Agent Status:** ✅ Running
- **Dashboard Status:** ✅ Running (HTTP 200)
- **Performance:** ~3% CPU, ~192MB memory

---

*Last Updated: December 11, 2025*
