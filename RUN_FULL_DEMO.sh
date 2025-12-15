#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

echo "============================================================"
echo " Linux Security Agent - FULL ONE-COMMAND DEMO"
echo "============================================================"
echo

########################################
# 1. Start agent + dashboard
########################################

echo ">>> STEP 1: Starting demo environment (agent + dashboard)"
echo
bash START_COMPLETE_DEMO.sh

echo
echo ">>> Waiting 30 seconds for baseline monitoring..."
sleep 30

########################################
# Helper: print stats from /api/agent/state
########################################
print_stats() {
  local label="$1"
  echo
  echo "[$label] /api/status"
  curl -s http://localhost:5001/api/status | python3 -m json.tool || echo "(status not available)"

  echo
  echo "[$label] /api/agent/state stats"
  curl -s http://localhost:5001/api/agent/state | python3 << 'PYEOF' || echo "(state not available)"
import sys, json
try:
    d = json.load(sys.stdin)
except Exception as e:
    print("Failed to parse state:", e)
    raise SystemExit(1)

s = d.get("stats", {})
print("  Processes    =", s.get("total_processes"))
print("  High Risk    =", s.get("high_risk"))
print("  Anomalies    =", s.get("anomalies"))
print("  Port Scans   =", s.get("port_scans"))
print("  C2 Beacons   =", s.get("c2_beacons"))
print("  Syscalls     =", s.get("total_syscalls"))
PYEOF
}

########################################
# 2. Snapshot BEFORE attacks
########################################

echo
echo "===== SNAPSHOT 1: BEFORE ATTACKS ====="
print_stats "BEFORE"

########################################
# 3. Run scripted attacks
########################################

echo
echo "============================================================"
echo ">>> STEP 2: Running safe attack simulations"
echo "============================================================"
echo

python3 scripts/simulate_attacks.py || echo "[WARN] simulate_attacks.py exited with non-zero status"

echo
echo ">>> Waiting 15 seconds for detections to be processed..."
sleep 15

########################################
# 4. Snapshot AFTER attacks
########################################

echo
echo "===== SNAPSHOT 2: AFTER ATTACKS ====="
print_stats "AFTER"

########################################
# 5. Show recent detection log lines
########################################

echo
echo "===== RECENT DETECTION LOGS ====="

LATEST_LOG=$(ls -t logs/security_agent_*.log 2>/dev/null | head -1 || true)
if [ -n "$LATEST_LOG" ]; then
  echo "[Using log file: $LATEST_LOG]"
  grep -E "PORT_SCANNING|HIGH RISK|ANOMALY|C2 BEACON" "$LATEST_LOG" 2>/dev/null | tail -20 || \
    echo "(no recent detection lines in last 20 entries)"
else
  echo "(no security_agent_*.log files found)"
fi

########################################
# 6. Final summary
########################################

echo
echo "============================================================"
echo " FULL DEMO COMPLETE"
echo " - Agent + dashboard started via START_COMPLETE_DEMO.sh"
echo " - Baseline stats captured (Snapshot 1)"
echo " - Attack simulations executed (scripts/simulate_attacks.py)"
echo " - Post-attack stats captured (Snapshot 2)"
echo " - Recent detection log lines shown"
echo "============================================================"
echo
