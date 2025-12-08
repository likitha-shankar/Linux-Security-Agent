# How Total Syscalls Count is Calculated

## Current Implementation

### Step 1: Agent Logs SCORE UPDATE
The agent logs SCORE UPDATE messages like:
```
📊 SCORE UPDATE: PID=286518 Process=pid_286518 Risk=19.9 Anomaly=52.7 Syscalls=100 TotalSyscalls=325 ConnectionBonus=0.0
```

### Step 2: Dashboard Receives Logs
- Dashboard receives logs via WebSocket from `web/app.py`
- `parse_log_line()` marks SCORE UPDATE logs as `type: 'score'`
- These logs are sent to the dashboard (even if not displayed in terminal)

### Step 3: Dashboard Parses TotalSyscalls
In `updateStats()` function (line 953-992):
```javascript
if (msg.includes('SCORE UPDATE')) {
    const totalSyscallsMatch = msg.match(/TotalSyscalls=(\d+)/);
    if (totalSyscallsMatch) {
        proc.syscalls = parseInt(totalSyscallsMatch[1]);
    }
    proc.lastSeen = now;
    processes.set(pid, proc);
}
```

### Step 4: Calculate Total
In `calculateCurrentStats()` function (line 891-943):
```javascript
let totalSyscalls = 0;
processes.forEach((proc, pid) => {
    const lastSeen = proc.lastSeen || 0;
    if (now - lastSeen < PROCESS_TIMEOUT_MS) {  // 60 seconds
        if (proc.syscalls) {
            totalSyscalls += proc.syscalls;  // Sum all active processes
        }
    }
});
```

## Why It Might Show 0

### Issue 1: Process Timeout
- Processes are considered "active" only if seen in last 60 seconds
- If a process hasn't sent a SCORE UPDATE in 60 seconds, it's excluded
- **Fix:** Processes might be timing out before syscalls accumulate

### Issue 2: SCORE UPDATE Not Reaching Dashboard
- SCORE UPDATE logs might be filtered out
- WebSocket might not be sending them
- **Check:** Verify logs are reaching dashboard

### Issue 3: Processes Map Not Updated
- If `proc.syscalls` is undefined or 0, it won't be added
- Processes might be removed from Map before syscalls are set
- **Fix:** Ensure syscalls are set before process times out

## Current Status
- ✅ Agent is logging TotalSyscalls (8,350 entries found)
- ✅ Parsing logic looks correct
- ⚠️  Dashboard showing 0 (likely process timeout issue)

## Recommended Fix
1. Increase PROCESS_TIMEOUT_MS from 60s to 120s (for longer-lived processes)
2. Or: Track cumulative syscalls separately (not per-process)
3. Or: Show "current session" syscalls (sum of all processes ever seen in this session)

