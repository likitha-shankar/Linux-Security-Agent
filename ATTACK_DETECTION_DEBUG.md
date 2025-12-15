# Attack Detection Debugging Guide

## Issue: Port Scans and C2 Beacons showing 0 in state file

### Root Causes

1. **Warm-up Period**: Agent suppresses detections during first 30 seconds
2. **Agent Not Running**: Attacks must happen while agent is running
3. **Port Simulation**: Agent uses simulated ports when real ports aren't available from auditd

### How to Test Properly

1. **Start the agent first:**
   ```bash
   cd ~/Linux-Security-Agent
   bash START_COMPLETE_DEMO.sh
   ```

2. **Wait for warm-up to pass (35+ seconds)**

3. **Run the test script:**
   ```bash
   python3 scripts/test_attack_detection.py
   ```

   This script:
   - Checks if agent is running
   - Waits for warm-up period
   - Tests port scanning (30 ports)
   - Tests C2 beaconing (15 beacons, 2.5s intervals)
   - Checks results from state file and logs

### Manual Testing

**Port Scanning:**
```bash
# Wait 35 seconds after agent starts, then:
python3 << 'EOF'
import socket, time
for port in range(5000, 5030):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.1)
        s.connect(('localhost', port))
        s.close()
    except: pass
    time.sleep(0.03)
print("Done")
EOF

# Wait 10 seconds, then check:
cat /tmp/security_agent_state.json | jq '.stats.port_scans'
```

**C2 Beaconing:**
```bash
# Wait 35 seconds after agent starts, then:
python3 << 'EOF'
import socket, time
for i in range(15):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.5)
        s.connect(('localhost', 4444))
        s.close()
    except: pass
    if i < 14: time.sleep(2.5)
print("Done")
EOF

# Wait 40 seconds, then check:
cat /tmp/security_agent_state.json | jq '.stats.c2_beacons'
```

### Checking Logs

```bash
# Find latest log
LOG=$(ls -t logs/security_agent_*.log | head -1)

# Check for detections
grep -c "PORT_SCANNING" $LOG
grep -c "C2_BEACONING" $LOG

# See recent detections
grep "PORT_SCANNING\|C2_BEACONING" $LOG | tail -5
```

### Why It Might Not Work

1. **Agent not running** - Check with `ps aux | grep simple_agent`
2. **Warm-up period** - Detections suppressed for first 30 seconds
3. **Port simulation** - Agent may not extract real ports from auditd, uses simulated ports
4. **Timing** - C2 needs 3+ connections with regular intervals (2.5s+)
5. **Thresholds** - Port scan needs 5+ unique ports

### Fixes Applied

1. ✅ C2 detection now filters by same destination port
2. ✅ Port scan threshold lowered to 5 ports
3. ✅ Test script ensures warm-up period passes
4. ✅ Better logging for debugging

### Next Steps

1. Pull latest code: `git pull`
2. Restart agent: `bash START_COMPLETE_DEMO.sh`
3. Wait 35 seconds
4. Run: `python3 scripts/test_attack_detection.py`
5. Check results in state file and logs
