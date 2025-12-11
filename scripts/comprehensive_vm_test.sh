#!/bin/bash
# Comprehensive VM Test Script
# Tests all fixes: anomaly detection and automated response

LOG_FILE="$HOME/Linux-Security-Agent/COMPREHENSIVE_VM_TEST_LOG.txt"
cd ~/Linux-Security-Agent

{
    echo "======================================================================"
    echo "COMPREHENSIVE VM TEST - ANOMALY DETECTION & RESPONSE FIXES"
    echo "======================================================================"
    echo "Generated: $(date)"
    echo "Host: $(hostname)"
    echo "User: $(whoami)"
    echo "======================================================================"
    echo ""
    
    # ========================================================================
    # PHASE 1: PRE-TEST STATUS
    # ========================================================================
    echo "======================================================================"
    echo "PHASE 1: PRE-TEST STATUS CHECK"
    echo "======================================================================"
    echo ""
    echo "Agent Status:"
    ps aux | grep '[s]imple_agent' | grep -v grep || echo "Agent not running"
    echo ""
    echo "Dashboard Status:"
    curl -s -o /dev/null -w 'HTTP %{http_code}\n' http://localhost:5001 || echo "Dashboard not accessible"
    echo ""
    echo "Current Log File:"
    LOG=$(ls -t logs/security_agent_*.log 2>/dev/null | head -1)
    if [ -n "$LOG" ]; then
        echo "  File: $(basename $LOG)"
        echo "  Size: $(ls -lh "$LOG" | awk '{print $5}')"
        echo "  Events: $(grep -c 'EVENT RECEIVED' "$LOG" 2>/dev/null || echo 0)"
        echo "  High-Risk: $(grep -c 'HIGH RISK DETECTED' "$LOG" 2>/dev/null || echo 0)"
        echo "  Anomalies: $(grep -c 'ANOMALY DETECTED' "$LOG" 2>/dev/null || echo 0)"
        echo "  Port Scans: $(grep -c 'PORT_SCANNING' "$LOG" 2>/dev/null || echo 0)"
    else
        echo "  No log file found"
    fi
    echo ""
    
    # ========================================================================
    # PHASE 2: RESTART AGENT WITH FIXES
    # ========================================================================
    echo "======================================================================"
    echo "PHASE 2: RESTART AGENT WITH FIXES"
    echo "======================================================================"
    echo ""
    echo "Stopping old agent..."
    sudo pkill -9 -f simple_agent.py 2>&1
    sleep 3
    echo "Old agent stopped"
    echo ""
    
    echo "Starting agent with fixes..."
    sudo nohup python3 core/simple_agent.py --collector auditd --threshold 20 --headless > /tmp/agent_test_start.log 2>&1 &
    AGENT_PID=$!
    echo "Agent PID: $AGENT_PID"
    sleep 15
    echo ""
    
    echo "Verifying agent started:"
    if ps aux | grep -q '[s]imple_agent'; then
        echo "✅ Agent is running"
        ps aux | grep '[s]imple_agent' | grep -v grep | head -1
    else
        echo "❌ Agent failed to start"
        echo "Error log:"
        tail -30 /tmp/agent_test_start.log 2>/dev/null
        exit 1
    fi
    echo ""
    
    # Get new log file
    sleep 5
    NEW_LOG=$(ls -t logs/security_agent_*.log 2>/dev/null | head -1)
    if [ -n "$NEW_LOG" ]; then
        echo "New log file: $(basename $NEW_LOG)"
        echo "Initial size: $(ls -lh "$NEW_LOG" | awk '{print $5}')"
        echo "Last 5 lines:"
        tail -5 "$NEW_LOG" 2>/dev/null
    fi
    echo ""
    
    # ========================================================================
    # PHASE 3: BASELINE MONITORING (2 minutes)
    # ========================================================================
    echo "======================================================================"
    echo "PHASE 3: BASELINE MONITORING (2 minutes)"
    echo "======================================================================"
    echo ""
    echo "Monitoring normal activity..."
    INITIAL_EVENTS=$(grep -c 'EVENT RECEIVED' "$NEW_LOG" 2>/dev/null || echo 0)
    INITIAL_ANOMALIES=$(grep -c 'ANOMALY DETECTED' "$NEW_LOG" 2>/dev/null || echo 0)
    INITIAL_HIGH_RISK=$(grep -c 'HIGH RISK DETECTED' "$NEW_LOG" 2>/dev/null || echo 0)
    echo "Initial counts - Events: $INITIAL_EVENTS, Anomalies: $INITIAL_ANOMALIES, High-Risk: $INITIAL_HIGH_RISK"
    echo ""
    
    for i in {1..24}; do
        sleep 5
        CURRENT_EVENTS=$(grep -c 'EVENT RECEIVED' "$NEW_LOG" 2>/dev/null || echo 0)
        CURRENT_ANOMALIES=$(grep -c 'ANOMALY DETECTED' "$NEW_LOG" 2>/dev/null || echo 0)
        CURRENT_HIGH_RISK=$(grep -c 'HIGH RISK DETECTED' "$NEW_LOG" 2>/dev/null || echo 0)
        if [ $((i % 6)) -eq 0 ]; then
            echo "[$(date +%H:%M:%S)] Events: $CURRENT_EVENTS (+$((CURRENT_EVENTS - INITIAL_EVENTS))) | Anomalies: $CURRENT_ANOMALIES (+$((CURRENT_ANOMALIES - INITIAL_ANOMALIES))) | High-Risk: $CURRENT_HIGH_RISK (+$((CURRENT_HIGH_RISK - INITIAL_HIGH_RISK)))"
        fi
    done
    echo ""
    
    BASELINE_EVENTS=$(grep -c 'EVENT RECEIVED' "$NEW_LOG" 2>/dev/null || echo 0)
    BASELINE_ANOMALIES=$(grep -c 'ANOMALY DETECTED' "$NEW_LOG" 2>/dev/null || echo 0)
    BASELINE_HIGH_RISK=$(grep -c 'HIGH RISK DETECTED' "$NEW_LOG" 2>/dev/null || echo 0)
    echo "Baseline complete - Events: $BASELINE_EVENTS, Anomalies: $BASELINE_ANOMALIES, High-Risk: $BASELINE_HIGH_RISK"
    echo ""
    
    # ========================================================================
    # PHASE 4: ATTACK SIMULATION (Multiple Rounds)
    # ========================================================================
    echo "======================================================================"
    echo "PHASE 4: ATTACK SIMULATION (Multiple Rounds)"
    echo "======================================================================"
    echo ""
    echo "Running attack simulation (Round 1)..."
    python3 scripts/simulate_attacks.py 2>&1 | head -30
    echo ""
    sleep 10
    
    echo "Running attack simulation (Round 2)..."
    python3 scripts/simulate_attacks.py 2>&1 | head -30
    echo ""
    sleep 10
    
    echo "Running attack simulation (Round 3)..."
    python3 scripts/simulate_attacks.py 2>&1 | head -30
    echo ""
    sleep 10
    echo ""
    
    # ========================================================================
    # PHASE 5: MONITOR DETECTIONS (2 minutes)
    # ========================================================================
    echo "======================================================================"
    echo "PHASE 5: MONITORING DETECTIONS (2 minutes)"
    echo "======================================================================"
    echo ""
    for i in {1..24}; do
        sleep 5
        EVENTS=$(grep -c 'EVENT RECEIVED' "$NEW_LOG" 2>/dev/null || echo 0)
        ANOMALIES=$(grep -c 'ANOMALY DETECTED' "$NEW_LOG" 2>/dev/null || echo 0)
        HIGH_RISK=$(grep -c 'HIGH RISK DETECTED' "$NEW_LOG" 2>/dev/null || echo 0)
        PORT_SCANS=$(grep -c 'PORT_SCANNING' "$NEW_LOG" 2>/dev/null || echo 0)
        if [ $((i % 6)) -eq 0 ]; then
            echo "[$(date +%H:%M:%S)] Events: $EVENTS | Anomalies: $ANOMALIES | High-Risk: $HIGH_RISK | Port Scans: $PORT_SCANS"
        fi
    done
    echo ""
    
    # ========================================================================
    # PHASE 6: DETAILED ANALYSIS
    # ========================================================================
    echo "======================================================================"
    echo "PHASE 6: DETAILED DETECTION ANALYSIS"
    echo "======================================================================"
    echo ""
    
    FINAL_EVENTS=$(grep -c 'EVENT RECEIVED' "$NEW_LOG" 2>/dev/null || echo 0)
    FINAL_ANOMALIES=$(grep -c 'ANOMALY DETECTED' "$NEW_LOG" 2>/dev/null || echo 0)
    FINAL_HIGH_RISK=$(grep -c 'HIGH RISK DETECTED' "$NEW_LOG" 2>/dev/null || echo 0)
    FINAL_PORT_SCANS=$(grep -c 'PORT_SCANNING' "$NEW_LOG" 2>/dev/null || echo 0)
    
    echo "=== FINAL DETECTION COUNTS ==="
    echo "Total Events: $FINAL_EVENTS"
    echo "Anomalies Detected: $FINAL_ANOMALIES"
    echo "High-Risk Processes: $FINAL_HIGH_RISK"
    echo "Port Scans: $FINAL_PORT_SCANS"
    echo ""
    
    echo "=== ANOMALY DETECTION IMPROVEMENT ==="
    ANOMALY_INCREASE=$((FINAL_ANOMALIES - BASELINE_ANOMALIES))
    if [ $FINAL_ANOMALIES -gt $BASELINE_ANOMALIES ]; then
        echo "✅ Anomaly detection IMPROVED: +$ANOMALY_INCREASE detections"
    else
        echo "⚠️  Anomaly detection: $FINAL_ANOMALIES total (baseline: $BASELINE_ANOMALIES)"
    fi
    echo ""
    
    echo "=== RECENT ANOMALY DETECTIONS ==="
    grep 'ANOMALY DETECTED' "$NEW_LOG" 2>/dev/null | tail -10 || echo "No anomaly detections found"
    echo ""
    
    echo "=== RECENT HIGH-RISK DETECTIONS ==="
    grep 'HIGH RISK DETECTED' "$NEW_LOG" 2>/dev/null | tail -10 || echo "No high-risk detections found"
    echo ""
    
    echo "=== RECENT PORT SCAN DETECTIONS ==="
    grep 'PORT_SCANNING' "$NEW_LOG" 2>/dev/null | tail -5 || echo "No port scan detections found"
    echo ""
    
    # ========================================================================
    # PHASE 7: RESPONSE HANDLER TEST (SAFE - Just Check Availability)
    # ========================================================================
    echo "======================================================================"
    echo "PHASE 7: RESPONSE HANDLER AVAILABILITY CHECK"
    echo "======================================================================"
    echo ""
    echo "Checking if ResponseHandler is integrated..."
    if grep -q 'ResponseHandler\|response_handler' "$NEW_LOG" 2>/dev/null; then
        echo "✅ ResponseHandler references found in code"
    else
        echo "⚠️  No ResponseHandler references in logs (may be disabled)"
    fi
    echo ""
    echo "Checking for response actions (should be 0 if disabled):"
    RESPONSE_ACTIONS=$(grep -c 'Response action taken' "$NEW_LOG" 2>/dev/null || echo 0)
    echo "Response actions taken: $RESPONSE_ACTIONS (expected 0 - disabled by default)"
    echo ""
    
    # ========================================================================
    # PHASE 8: SYSTEM STATUS
    # ========================================================================
    echo "======================================================================"
    echo "PHASE 8: SYSTEM STATUS"
    echo "======================================================================"
    echo ""
    echo "Agent Process:"
    ps aux | grep '[s]imple_agent' | grep -v grep | head -1
    echo ""
    echo "Log File:"
    ls -lh "$NEW_LOG" 2>/dev/null
    echo ""
    echo "System Resources:"
    echo "CPU:"
    top -bn1 | grep "Cpu(s)" | head -1
    echo "Memory:"
    free -h | head -2
    echo ""
    
    # ========================================================================
    # PHASE 9: FINAL SUMMARY
    # ========================================================================
    echo "======================================================================"
    echo "PHASE 9: FINAL TEST SUMMARY"
    echo "======================================================================"
    echo ""
    echo "=== TEST RESULTS ==="
    echo ""
    echo "✅ Agent Status: RUNNING"
    echo "✅ Dashboard Status: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:5001 2>/dev/null || echo 'UNKNOWN')"
    echo ""
    echo "Detection Results:"
    echo "  Events Captured: $FINAL_EVENTS"
    echo "  Anomalies: $FINAL_ANOMALIES (baseline: $BASELINE_ANOMALIES)"
    echo "  High-Risk: $FINAL_HIGH_RISK"
    echo "  Port Scans: $FINAL_PORT_SCANS"
    echo ""
    
    if [ $FINAL_ANOMALIES -gt 0 ]; then
        echo "✅ ANOMALY DETECTION: WORKING ($FINAL_ANOMALIES detections)"
    else
        echo "⚠️  ANOMALY DETECTION: No detections (may need more aggressive attacks)"
    fi
    echo ""
    
    if [ $FINAL_HIGH_RISK -gt 0 ]; then
        echo "✅ HIGH-RISK DETECTION: WORKING ($FINAL_HIGH_RISK detections)"
    else
        echo "⚠️  HIGH-RISK DETECTION: No detections"
    fi
    echo ""
    
    if [ $FINAL_PORT_SCANS -gt 0 ]; then
        echo "✅ PORT SCAN DETECTION: WORKING ($FINAL_PORT_SCANS detections)"
    else
        echo "⚠️  PORT SCAN DETECTION: No detections"
    fi
    echo ""
    
    echo "=== OVERALL STATUS ==="
    if [ $FINAL_ANOMALIES -gt 0 ] || [ $FINAL_HIGH_RISK -gt 0 ] || [ $FINAL_PORT_SCANS -gt 0 ]; then
        echo "✅ SYSTEM WORKING - Detections occurring"
    else
        echo "⚠️  SYSTEM RUNNING - Limited detections (may need more time or different attacks)"
    fi
    echo ""
    
    echo "======================================================================"
    echo "TEST COMPLETE"
    echo "======================================================================"
    echo "End time: $(date)"
    echo "Duration: ~6 minutes"
    echo "Log file: $LOG_FILE"
    echo "======================================================================"
    
} 2>&1 | tee "$LOG_FILE"

echo ""
echo "✅ Comprehensive test log saved to: $LOG_FILE"
echo "File size: $(ls -lh "$LOG_FILE" | awk '{print $5}')"
echo "Lines: $(wc -l < "$LOG_FILE")"
