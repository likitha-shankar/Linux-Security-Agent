# Why Dashboard Updates May Not Be Visible

## How Dashboard Updates Work

1. **Automatic Polling**: The dashboard polls `/api/agent/state` every **2 seconds** automatically
2. **State File**: The agent writes its state to `/tmp/security_agent_state.json`
3. **API Endpoint**: The dashboard reads from the state file via `/api/agent/state`
4. **UI Update**: When the API returns new data, the dashboard updates the numbers

## Why You Might Not See Updates

### 1. Agent Not Running
- **Symptom**: Dashboard shows all zeros
- **Check**: Open browser console (F12) - you'll see `[Dashboard] No state received - agent may not be running`
- **Fix**: Start the agent: `bash START_COMPLETE_DEMO.sh`

### 2. State File Not Updating
- **Symptom**: Attacks detected in logs but dashboard shows 0
- **Check**: Look for `State BEFORE write` and `State AFTER write` in agent logs
- **Fix**: This was a deadlock bug - **FIXED** in latest code. Pull latest: `git pull`

### 3. Dashboard Not Polling
- **Symptom**: Numbers never change even when agent is running
- **Check**: Open browser console (F12) - you should see logs every 2 seconds
- **Fix**: Refresh the page, check browser console for errors

### 4. Warm-up Period
- **Symptom**: Attacks happen but dashboard shows 0
- **Check**: Agent suppresses detections for first 30 seconds (warm-up)
- **Fix**: Wait 35 seconds after starting agent before testing attacks

## How to Verify Dashboard is Working

1. **Open Browser Console** (F12 → Console tab)
2. **Look for logs**:
   - `[Dashboard] Current stats: ...` (every ~20 seconds)
   - `[Dashboard] ⚠️ ATTACK COUNT CHANGED: ...` (when attacks detected)
3. **Check Network Tab** (F12 → Network tab):
   - Filter by "state"
   - You should see `/api/agent/state` requests every 2 seconds
   - Click on one → Response tab → Should show JSON with stats

## Testing Dashboard Updates

1. **Start Agent**:
   ```bash
   cd ~/Linux-Security-Agent
   bash START_COMPLETE_DEMO.sh
   ```

2. **Wait 40 seconds** for warm-up

3. **Open Dashboard** in browser:
   ```
   http://<VM_IP>:5001
   ```

4. **Open Browser Console** (F12)

5. **Run Attack Test**:
   ```bash
   python3 scripts/test_attack_detection.py
   ```

6. **Watch Console**: You should see:
   - `[Dashboard] ⚠️ ATTACK COUNT CHANGED: 0 → 1`
   - Numbers updating in the dashboard

## Expected Behavior

- ✅ Dashboard polls every 2 seconds
- ✅ When state file updates, dashboard shows new values within 2 seconds
- ✅ Console logs show when attacks are detected
- ✅ Attack count increases when port scans or C2 beacons are detected

## Troubleshooting

If dashboard still doesn't update:

1. **Check Agent Status**:
   ```bash
   ps aux | grep simple_agent
   ```

2. **Check State File**:
   ```bash
   cat /tmp/security_agent_state.json | jq '.stats'
   ```

3. **Check Dashboard API**:
   ```bash
   curl http://localhost:5001/api/agent/state | jq '.stats'
   ```

4. **Check Browser Console** for JavaScript errors

5. **Check Agent Logs**:
   ```bash
   LOG=$(ls -t logs/security_agent_*.log | head -1)
   grep "State BEFORE write\|State AFTER write" $LOG
   ```
