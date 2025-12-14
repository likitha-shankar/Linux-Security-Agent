## Manual verification steps

### Step 1: Check if the dashboard is running

**On the VM (via Google Cloud Console SSH or your terminal):**

```bash
# Check if dashboard process is running
ps aux | grep app.py | grep -v grep

# Should show something like:
# likitha+  XXXXX  0.2  1.9 146864 76144 ... python3 app.py
```

**If not running, start it:**
```bash
cd ~/Linux-Security-Agent/web
nohup python3 app.py > /tmp/dashboard.log 2>&1 &
```

---

### Step 2: Check if the agent is running

```bash
# Check agent process
ps aux | grep simple_agent.py | grep -v grep | grep python3

# Should show the agent running
```

**If not running, start it:**
```bash
cd ~/Linux-Security-Agent
sudo nohup python3 core/simple_agent.py --collector ebpf --threshold 20 --headless > /dev/null 2>&1 &
```

---

### Step 3: Check if port 5001 is listening

```bash
# Check if port is open
ss -tlnp | grep :5001
# OR
netstat -tlnp | grep :5001

# Should show:
# LISTEN 0 50 0.0.0.0:5001 0.0.0.0:* users:(("python3",pid=XXXXX,fd=3))
```

---

### Step 4: Test the dashboard API

```bash
# Test status endpoint
curl http://localhost:5001/api/status

# Should return:
# {"monitoring":true,"pid":XXXXX,"running":true}

# Test state endpoint
curl http://localhost:5001/api/agent/state | python3 -m json.tool | head -20

# Should show JSON with processes, stats, etc.
```

---

### Step 5: Check the state file

```bash
# Check if state file exists and is recent
ls -lh /tmp/security_agent_state.json

# Should show file with size ~20-25K, updated recently

# Check if JSON is valid
python3 -c "import json; f=open('/tmp/security_agent_state.json'); d=json.load(f); print(f'✅ Valid JSON - Processes: {len(d.get(\"processes\", []))}')"

# Should show number of processes (not 0)
```

---

### Step 6: Check agent logs

```bash
# Find latest log file
LATEST_LOG=$(ls -t ~/Linux-Security-Agent/logs/security_agent_*.log | head -1)
echo "Latest log: $LATEST_LOG"

# Check recent activity
tail -20 "$LATEST_LOG" | grep -E "(SCORE UPDATE|HIGH RISK|ANOMALY)"

# Should show recent log entries
```

---

### Step 7: Test dashboard access

**From your local machine:**

```bash
# Test direct access (if firewall allows)
curl http://136.112.137.224:5001/api/status

# OR use SSH port forwarding
ssh -L 5001:localhost:5001 -i ~/.ssh/vm_access_key likithashankar14@136.112.137.224

# Then in another terminal:
curl http://localhost:5001/api/status
```

---

### Step 8: Check browser access

1. Open browser
2. Go to: `http://136.112.137.224:5001`
3. Open Developer Tools (F12)
4. Go to Console tab
5. Check for errors (red text)
6. Go to Network tab
7. Refresh page (Ctrl+F5 or Cmd+Shift+R)
8. Look for:
   - `api/status` - should return 200
   - `api/agent/state` - should return 200 with JSON data
   - `dashboard.html` - should return 200

---

### Step 9: Verify dashboard data

**In browser console (F12 → Console), run:**

```javascript
// Test if sync function exists
typeof syncAgentState

// Should return: "function"

// Manually trigger sync
syncAgentState()

// Check if data is being fetched
fetch('/api/agent/state')
  .then(r => r.json())
  .then(d => console.log('State data:', d.stats, 'Processes:', d.processes.length))
```

---

### Step 10: Check for common issues

**Issue 1: Dashboard shows all zeros**
- Solution: Hard refresh (Ctrl+F5 or Cmd+Shift+R)
- Check browser console for JavaScript errors
- Verify `api/agent/state` returns data

**Issue 2: "Disconnected from dashboard" messages**
- Check if dashboard process is running (Step 1)
- Check dashboard logs: `tail -f /tmp/dashboard.log`

**Issue 3: State file not updating**
- Check agent is running (Step 2)
- Check agent logs for errors (Step 6)
- Verify state file permissions: `ls -l /tmp/security_agent_state.json`

**Issue 4: API returns errors**
- Check dashboard logs: `tail -20 /tmp/dashboard.log`
- Verify state file is valid JSON (Step 5)
- Restart dashboard if needed

---

### Quick health check script

**Run this on the VM to check everything at once:**

```bash
echo "=== Health Check ==="
echo ""
echo "1. Dashboard:" && (ps aux | grep app.py | grep -v grep > /dev/null && echo "✅ Running" || echo "❌ Not running")
echo "2. Agent:" && (ps aux | grep simple_agent.py | grep -v grep | grep python3 > /dev/null && echo "✅ Running" || echo "❌ Not running")
echo "3. Port 5001:" && (ss -tlnp | grep :5001 > /dev/null && echo "✅ Listening" || echo "❌ Not listening")
echo "4. State File:" && ([ -f /tmp/security_agent_state.json ] && echo "✅ Exists" || echo "❌ Missing")
echo "5. API Status:" && (curl -s http://localhost:5001/api/status > /dev/null && echo "✅ Responding" || echo "❌ Not responding")
echo "6. API State:" && (curl -s http://localhost:5001/api/agent/state | python3 -c "import sys, json; d=json.load(sys.stdin); print(f'✅ OK - {len(d.get(\"processes\", []))} processes')" 2>/dev/null || echo "❌ Error")
```

---

### If something is broken

**Restart everything:**

```bash
# Kill everything
sudo pkill -9 -f simple_agent.py
pkill -9 -f app.py
sleep 2

# Clean state file
rm -f /tmp/security_agent_state.json

# Start agent
cd ~/Linux-Security-Agent
sudo nohup python3 core/simple_agent.py --collector ebpf --threshold 20 --headless > /dev/null 2>&1 &
sleep 5

# Start dashboard
cd ~/Linux-Security-Agent/web
nohup python3 app.py > /tmp/dashboard.log 2>&1 &
sleep 3

# Verify
ps aux | grep -E "(simple_agent|app.py)" | grep -v grep
```

---

### Expected results

- Dashboard process: Running
- Agent process: Running
- Port 5001: Listening
- State file: Exists, valid JSON, recent timestamp
- API /status: Returns `{"monitoring":true,"pid":XXX,"running":true}`
- API /agent/state: Returns JSON with processes and stats
- Browser: Shows data (not all zeros) after hard refresh

Follow these steps and note any failures.