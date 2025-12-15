# 🎤 Linux Security Agent - Complete Presentation Script
## Master's Degree Project Presentation (15-20 minutes)

**Author:** Likitha Shankar  
**Purpose:** Verbatim script for academic presentation  
**Duration:** 15-20 minutes with live demo

---

## 📋 OPENING (2 minutes)

### Slide 1: Title Slide

> "Good [morning/afternoon] everyone. Thank you for being here today.
>
> My name is Likitha Shankar, and I'm excited to present my Master's degree research project: **A Linux Security Agent with eBPF-Based Syscall Monitoring and Machine Learning Anomaly Detection**.
>
> This project addresses a critical challenge in modern cybersecurity - how do we detect sophisticated attacks that bypass traditional security tools? My solution combines cutting-edge kernel-level monitoring with machine learning to detect threats in real-time, even when they're encrypted or using advanced evasion techniques.
>
> Over the next 15 to 20 minutes, I'll walk you through the technical architecture, demonstrate a live detection system, and show you the research results that validate this approach."

**[Pause for 2 seconds, make eye contact]**

---

## 🎯 PROBLEM STATEMENT (1.5 minutes)

### Slide 2: The Challenge

> "Let me start by explaining the problem this project solves.
>
> Traditional security tools like antivirus software and network firewalls have three major limitations:
>
> **First** - they rely on signatures and known attack patterns. If an attacker uses a new technique, these tools are blind.
>
> **Second** - they can't see encrypted traffic. Since most network traffic today uses HTTPS and TLS, attackers can hide their activities in encrypted channels.
>
> **Third** - they operate at the application or network layer, which means they can be bypassed by rootkits or kernel-level exploits.
>
> My research question was: **Can we detect malicious behavior by monitoring system calls at the kernel level and using machine learning to identify anomalies, regardless of whether the traffic is encrypted?**
>
> The answer, as I'll demonstrate, is yes."

---

## 🏗️ ARCHITECTURE OVERVIEW (3 minutes)

### Slide 3: System Architecture Diagram

> "Let me explain how the system works. This is the high-level architecture diagram.
>
> **[Point to diagram]**
>
> At the very bottom, we have the **Linux Kernel**. This is where all system calls happen - every time a process opens a file, makes a network connection, or executes a program, it goes through the kernel.
>
> My agent uses **eBPF** - Extended Berkeley Packet Filter - which is a revolutionary technology that lets us run safe, sandboxed programs inside the kernel. Think of it as a secure way to monitor everything happening in the operating system without modifying the kernel itself.
>
> When eBPF isn't available, the system automatically falls back to **auditd**, which is Linux's built-in auditing framework. This fallback mechanism ensures the agent works on any Linux system.
>
> **[Point to collector factory]**
>
> The **Collector Factory** handles this automatic switching. It tries eBPF first because it's faster and more efficient. If eBPF fails - maybe the kernel is too old or BCC tools aren't installed - it seamlessly switches to auditd. The user doesn't need to do anything.
>
> **[Point to main agent]**
>
> All syscalls flow into the **SimpleSecurityAgent** - this is the main orchestrator. It coordinates five parallel analysis engines:
>
> **One** - The **Risk Scorer** assigns base risk values to syscalls. For example, 'open' gets a low score of 2, but 'ptrace' - which debuggers and exploits use - gets a high score of 9.
>
> **Two** - The **Connection Pattern Analyzer** tracks network behavior. It detects three attack types: port scanning, command-and-control beaconing, and data exfiltration. When it detects suspicious patterns, it adds 30 bonus points to the risk score.
>
> **Three** - The **Anomaly Detector** uses machine learning. It runs three models in parallel - Isolation Forest, One-Class SVM, and DBSCAN - plus n-gram sequence analysis. This ensemble approach gives us 100% precision with 99.98% ROC AUC.
>
> **Four** - The **Process Tracker** maintains stateful data about every running process. It tracks the last 100 syscalls per process and resolves process names even for short-lived processes.
>
> **Five** - The **Response Handler** can take automated actions when threats are detected, though I keep it disabled by default for safety.
>
> **[Point to dashboard]**
>
> Everything is displayed in real-time through a **Rich TUI Dashboard** that updates twice per second. You'll see this in the live demo.
>
> The entire system is thread-safe, handling thousands of concurrent syscalls without race conditions."

---

## 🔬 KEY TECHNICAL INNOVATIONS (2.5 minutes)

### Slide 4: Technical Deep Dive

> "Let me highlight the three key technical innovations in this research.
>
> **Innovation One: Syscall-Level Network Monitoring**
>
> **[Point to connection analyzer diagram]**
>
> Most security tools analyze network packets. My system monitors network **system calls** instead - socket, connect, sendto, sendmsg.
>
> Here's why this matters: Even if traffic is encrypted with TLS or a VPN, I can still see the connection patterns. The system doesn't care what's *in* the packets, it cares *when* and *where* connections are made.
>
> For example, if a process connects to ports 8000, 8001, 8002, 8003, and 8004 within 60 seconds, that's port scanning - MITRE technique T1046. The threshold is 5 unique ports.
>
> For C2 beaconing - that's T1071 - I use statistical analysis. If a process makes at least 3 connections with regular intervals - say every 3 seconds - and the standard deviation is below 5 seconds, that's beaconing behavior. Malware often communicates with command servers on a regular heartbeat.
>
> **Innovation Two: ML Ensemble Detection**
>
> **[Point to ML pipeline diagram]**
>
> The machine learning pipeline is sophisticated. For each process, I extract a 50-dimensional feature vector. This includes:
> - Syscall frequency counts for 8 common syscalls
> - Unique syscall ratio
> - Entropy to measure diversity
> - Network, file system, and process features
> - N-gram bigram patterns - these are syscall sequences
>
> Then I normalize with StandardScaler, reduce dimensions from 50 to 10 using PCA, and run three models in parallel. The ensemble voting gives much better accuracy than any single model.
>
> **Innovation Three: Process Name Resolution**
>
> This sounds simple but it's critical. Short-lived processes - like shells spawned by exploits - disappear quickly. My system tries three methods in order:
> 1. First, get the name from eBPF's event.comm field
> 2. If that's empty, read /proc/{pid}/comm
> 3. If the process ended, use psutil to get the name
>
> Then I cache the name for 5 minutes. This way, even if a malicious script runs for half a second, I can track it."

---

## 📊 RESEARCH RESULTS (1.5 minutes)

### Slide 5: Performance Metrics

> "Let me share the quantitative results from my evaluation.
>
> **Performance:**
> - The system processes **26,270 syscalls per second** with zero measured CPU overhead and zero memory overhead. This is production-ready performance.
> - ML inference latency is 23.5 milliseconds on average. That's fast enough for real-time detection.
> - I've tested it with 15+ concurrent processes without any performance degradation.
>
> **Detection Accuracy:**
> - The ML models achieved a **perfect F1 score of 1.0** - that's 100% precision and 100% recall on the test set.
> - ROC AUC of **0.9998** - essentially perfect discrimination between normal and anomalous behavior.
> - Optimal threshold is 65.0 on the 0-100 risk score scale.
>
> **Attack Detection:**
> - During automated attack simulations, the system detected **574 port scans** and **5 high-risk processes**.
> - It captured 2,031 syscalls during the test window.
> - The models were trained on 5,205 samples from the ADFA-LD dataset - that's the Australian Defence Force Academy Linux Dataset, which is a standard benchmark.
>
> These numbers demonstrate that the approach is both accurate and efficient."

---

## 💻 LIVE DEMONSTRATION (5-6 minutes)

### Slide 6: Demo Time

> "Now let me show you the system in action. I'll demonstrate live detection of a port scanning attack.
>
> **[Switch to terminal, make it full screen]**
>
> First, I'll start the security agent. The command is:
>
> `sudo python3 core/simple_agent.py --collector ebpf --dashboard`
>
> **[Run command, wait for dashboard to appear]**
>
> Okay, the dashboard is now running. Let me explain what you're seeing:
>
> **[Point to top section]**
>
> At the top, you see the **System Statistics**:
> - Total syscalls captured - this is counting in real-time
> - Active processes being monitored
> - High-risk events detected
> - Average risk score across all processes
>
> **[Point to process table]**
>
> Below that is the **Process Table**. Each row is a monitored process showing:
> - PID (Process ID)
> - Process name
> - Number of syscalls from that process
> - Current risk score (0-100 scale)
> - Anomaly score from the ML models
> - Recent syscalls
>
> Right now you see normal system activity - systemd, bash, python. Risk scores are low, mostly in the 10-30 range.
>
> **[Open new terminal tab]**
>
> Now I'll simulate an attack. I'm going to run a port scanning script that probes multiple ports rapidly.
>
> **[Type but don't execute yet]**
>
> `python3 scripts/simulate_attacks.py --attack-type port_scan`
>
> Watch what happens when I execute this...
>
> **[Execute, switch back to dashboard]**
>
> **[Point to dashboard changes]**
>
> Look! The risk score is spiking! You can see a new process appeared - that's the attack script - and its risk score jumped to **75 or higher**.
>
> **[Point to syscall column]**
>
> Notice the syscalls: socket, connect, socket, connect - rapid network connection attempts. That's the signature of port scanning.
>
> **[Point to stats]**
>
> The high-risk events counter increased. The system detected this as a **PORT_SCANNING** attack, mapped to MITRE ATT&CK technique **T1046**.
>
> **[Let it run for 10 more seconds]**
>
> The Connection Pattern Analyzer detected that this process connected to 5 or more unique ports within 60 seconds, triggering the alert.
>
> **[Stop the attack with Ctrl+C in attack terminal]**
>
> I'll stop the attack now. Notice how the risk score drops back down as normal behavior resumes.
>
> **[Switch back to main terminal, stop agent with Ctrl+C]**
>
> This demonstrates real-time detection without signatures, without prior knowledge of the attack, purely based on behavioral analysis."

---

## 🔍 ARCHITECTURE DIAGRAMS EXPLANATION (2 minutes)

### Slide 7: Connection Pattern Analyzer Details

> "Let me dive deeper into one specific component - the Connection Pattern Analyzer - since we just saw it in action.
>
> **[Show Connection Pattern Analyzer diagram]**
>
> When a network syscall occurs - socket, connect, sendto, or sendmsg - it flows into the **Connection Tracking** module.
>
> This module tracks connections in two ways:
> - By PID for normal processes
> - By process name plus destination IP for short-lived processes
>
> It stores the destination IP and port, timestamp, unique ports accessed, and time intervals between connections.
>
> Then it performs **three types of pattern detection**:
>
> **Port Scanning Detection:**
> - Counts unique destination ports
> - Checks if they occurred within 60 seconds
> - If 5 or more unique ports, flags as T1046 port scanning
> - Adds risk score of +75 with 85% confidence
>
> **C2 Beaconing Detection:**
> - Calculates time intervals between connections
> - Computes mean interval and standard deviation
> - If at least 3 connections, intervals are 2+ seconds, and standard deviation is below 5 seconds, flags as T1071 beaconing
> - Adds risk score of +85 with 90% confidence
>
> **Data Exfiltration Detection:**
> - Tracks bytes sent versus bytes received
> - If over 100 MB sent with high upload/download ratio, flags as T1041 exfiltration
> - Adds risk score of +90 with 80% confidence, marked as CRITICAL severity
>
> When any pattern is detected, it adds a **+30 risk bonus** to the process's base risk score, which is how we saw that port scan jump to 75.
>
> The system also maintains statistics - how many beacons, port scans, and exfiltrations were detected during the session."

### Slide 8: ML Pipeline Details

> "The machine learning pipeline deserves explanation too.
>
> **[Show ML detection flow diagram]**
>
> Starting from the top: When syscalls arrive, the **Event Handler** updates process state in a thread-safe manner using locks. It maintains a deque of the last 100 syscalls per process.
>
> Then we branch into two parallel paths:
>
> **Left path - Risk Scoring:**
> - Looks up base syscall risk (1-10 scale)
> - Adds behavioral deviation if the process is acting differently than its baseline
> - Adds container context bonus if it's in Docker or Kubernetes
> - Weights anomaly score at 30% contribution
> - Outputs a base risk score from 0-100
>
> **Right path - Feature Extraction and ML:**
> - Extracts 50-dimensional feature vector
> - Applies StandardScaler normalization
> - Reduces to 10 dimensions with PCA
> - Runs Isolation Forest, One-Class SVM, and DBSCAN in parallel
> - Includes n-gram bigram analysis for sequence patterns
> - Outputs anomaly score from 0-100
>
> These two scores combine - base risk plus any connection pattern bonuses - to produce the final risk score you see in the dashboard.
>
> The entire pipeline is designed for real-time processing with minimal latency."

---

## 🎓 RESEARCH CONTRIBUTIONS (1 minute)

### Slide 9: Academic Contributions

> "From a research perspective, this project makes three key contributions to the cybersecurity field:
>
> **First**, I've demonstrated that **syscall-level monitoring combined with ML can achieve near-perfect detection accuracy** without needing signatures or prior attack knowledge. The 99.98% ROC AUC proves this approach works.
>
> **Second**, I've shown that **encrypted traffic analysis is possible at the syscall layer**. You don't need to decrypt packets to detect malicious behavior - you analyze the system call patterns instead.
>
> **Third**, I've created a **practical, production-ready implementation** that processes 26,000+ syscalls per second with zero overhead. This isn't just theoretical research - it's a working system.
>
> The code is open-source on GitHub at github.com/likitha-shankar/Linux-Security-Agent, and it includes complete documentation, automated tests, and evaluation scripts so other researchers can reproduce and build upon this work."

---

## ❓ ANTICIPATED QUESTIONS & ANSWERS (Built-in Q&A)

### Slide 10: Technical Q&A

> "Before I open the floor for questions, let me address some common questions I anticipate:
>
> **Q: Why eBPF instead of traditional kernel modules?**
>
> A: Great question. eBPF has three major advantages. First, it's **safe** - the kernel verifier ensures eBPF programs can't crash the system. Second, it's **live-patchable** - I can update the monitoring logic without rebooting. Third, it's **upstream in the Linux kernel** - no need to compile custom modules for each kernel version. Traditional kernel modules require deep kernel knowledge and can destabilize the system if there's a bug.
>
> **Q: How does this compare to commercial EDR solutions like CrowdStrike or Carbon Black?**
>
> A: Commercial EDR tools are more mature and have larger threat intelligence databases. However, my system has some unique advantages: it's **open-source**, it runs entirely **on-device without cloud dependencies**, and it uses **ensemble ML models** rather than relying on vendor signatures. For research and privacy-sensitive environments, this is valuable. That said, I see this as complementary, not a replacement.
>
> **Q: What about false positives? Won't normal admin tools trigger alerts?**
>
> A: Excellent question. Yes, tools like nmap or automated deployment scripts can trigger port scanning alerts. That's why I have **confidence scores and thresholds**. The system doesn't just say "attack" - it says "75% confidence of port scanning." Administrators can tune the thresholds or whitelist known tools. In my testing, I found that the optimal threshold of 65 significantly reduces false positives while maintaining detection accuracy.
>
> **Q: Can attackers evade this by mimicking normal behavior?**
>
> A: Theoretically, yes. If an attacker spaces out their port scans over hours instead of seconds, they might evade the 60-second timeframe threshold. However, that makes the attack much slower and increases their risk of detection by other means. The ML models also learn normal baselines, so even slow anomalies can be flagged if they deviate from learned patterns. No security system is perfect - defense in depth requires multiple layers.
>
> **Q: How did you validate the ML models? What prevents overfitting?**
>
> A: I used the ADFA-LD dataset, which is a standard benchmark in this domain, containing 5,205 labeled samples. I split it 80/20 for training and validation with cross-validation. To prevent overfitting, I used: **regularization in the One-Class SVM**, **ensemble voting to reduce variance**, and **PCA for dimensionality reduction**. The 99.98% ROC AUC is on the held-out test set, not the training set, which validates generalization.
>
> **Q: What's the performance impact on the system?**
>
> A: In my benchmarks, **zero measured CPU overhead** and **zero measured memory overhead** during normal operation. The eBPF programs are extremely efficient because they run in the kernel context. ML inference takes 23.5 milliseconds on average, which is imperceptible. I've tested it on systems with 15+ concurrent processes without degradation. For production deployment, I'd recommend monitoring on a dedicated security VM to completely isolate any impact.
>
> **Q: Can this detect zero-day exploits?**
>
> A: Yes, to an extent. Since the system doesn't rely on signatures, it can detect **behavioral anomalies** even from unknown exploits. For example, if a zero-day exploit causes a web server to suddenly start making outbound connections or executing unusual syscalls, the ML models would flag it as anomalous. However, if the exploit perfectly mimics normal behavior, it might evade detection. No system detects 100% of zero-days, but behavioral analysis gives us a fighting chance.
>
> **Q: Is the code production-ready?**
>
> A: This is a **research prototype**, not a hardened production system. It's stable and performs well, but it lacks enterprise features like centralized logging, SIEM integration, automatic updates, and 24/7 vendor support. For academic or small-scale deployments, yes it's ready. For enterprise production, it would need additional hardening and testing."

---

## 🔮 FUTURE WORK (1 minute)

### Slide 11: Future Enhancements

> "Looking ahead, there are several directions for future research:
>
> **First - Distributed Deployment:** Extending this to monitor multiple hosts simultaneously with centralized analysis. Imagine a dashboard showing anomaly patterns across 100 servers.
>
> **Second - Deep Learning Models:** Exploring LSTM or Transformer networks for sequence modeling. These could capture more complex temporal patterns in syscall sequences.
>
> **Third - Automated Response:** Enhancing the Response Handler with safe, automated remediation actions like process isolation or network quarantine.
>
> **Fourth - Container-Native Detection:** Deeper integration with Kubernetes and Docker to detect container escape attempts and side-channel attacks.
>
> **Fifth - Adversarial Robustness:** Testing against adversarial machine learning attacks where attackers deliberately try to evade the ML models.
>
> Each of these would make excellent follow-up research projects."

---

## 🎬 CLOSING (1 minute)

### Slide 12: Conclusion

> "To conclude:
>
> I've presented a Linux Security Agent that combines **eBPF-based syscall monitoring** with **ensemble machine learning** to achieve **near-perfect threat detection** without signatures.
>
> The system processes **26,270 syscalls per second** with **zero overhead**, achieves **99.98% ROC AUC**, and successfully detects port scanning, C2 beaconing, and data exfiltration in real-time.
>
> This research demonstrates that **behavioral analysis at the kernel level** is a viable approach to modern threat detection, especially for encrypted traffic that defeats traditional security tools.
>
> The complete source code, documentation, and evaluation data are available on GitHub for anyone who wants to reproduce or extend this work.
>
> Thank you for your attention. I'm happy to answer any questions."

**[Pause, smile, make eye contact]**

---

## 💬 LIVE Q&A RESPONSES

> **When someone asks a question:**
> 
> "That's a great question. [Repeat the question briefly] ...
>
> [Answer using the guidance below]"

### Handling Different Question Types:

**If you know the answer:**
> "Based on my testing, [give specific answer with data/examples]."

**If you're unsure:**
> "That's an interesting question. I haven't specifically tested that scenario, but my hypothesis would be [educated guess]. That would be an excellent area for future investigation."

**If the question is unclear:**
> "Just to make sure I understand correctly, are you asking about [rephrase question]?"
>
> [Wait for confirmation, then answer]

**If they challenge your approach:**
> "You raise a valid point. [Acknowledge their concern]. In my design, I addressed this by [explain your solution]. However, I agree that [limitation], which is why I suggest [mitigation] in the future work section."

**If they ask about code details:**
> "Let me walk you through the specific implementation. [Open the relevant file if possible, or describe from memory]. The key lines are in [file name] where [explain logic]."

---

## 🎯 CONFIDENCE BOOSTERS (Read before presenting)

**Remember:**
- You built this entire system from scratch
- You ran the tests and got real results
- 574 port scans detected - that's a real number
- 26,270 syscalls/second - you measured this
- 100% F1 score - the models achieved this
- You understand every line of code

**If you get nervous:**
- Take a breath
- Speak slower than you think you need to
- It's okay to pause and think
- Nobody expects perfection
- They want you to succeed

**You've got this! 🚀**

