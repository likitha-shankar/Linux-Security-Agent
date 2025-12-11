#!/bin/bash
# Comprehensive Fix Verification Script
# Tests anomaly detection improvements and automated response integration

LOG_FILE="$HOME/Linux-Security-Agent/COMPREHENSIVE_FIX_VERIFICATION.txt"
cd ~/Linux-Security-Agent

{
    echo "======================================================================"
    echo "COMPREHENSIVE FIX VERIFICATION TEST"
    echo "======================================================================"
    echo "Generated: $(date)"
    echo "Host: $(hostname)"
    echo "Purpose: Verify anomaly detection and automated response fixes"
    echo "======================================================================"
    echo ""
    
    # ========================================================================
    # PHASE 1: PRE-TEST STATUS
    # ========================================================================
    echo "======================================================================"
    echo "PHASE 1: PRE-TEST STATUS CHECK"
    echo "======================================================================"
    echo ""
    echo "Command: Checking agent status..."
    if ps aux | grep -q '[s]imple_agent'; then
        echo "✅ Agent is RUNNING"
        ps aux | grep '[s]imple_agent' | grep -v grep | head -1
    else
        echo "❌ Agent NOT running"
        exit 1
    fi
    echo ""
    
    echo "Command: Checking dashboard status..."
    HTTP_CODE=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:5001 2>/dev/null)
    if [ "$HTTP_CODE" = "200" ]; then
        echo "✅ Dashboard RUNNING (HTTP $HTTP_CODE)"
    else
        echo "⚠️  Dashboard status: HTTP $HTTP_CODE"
    fi
    echo ""
    
    LOG=$(ls -t logs/security_agent_*.log 2>/dev/null | head -1)
    if [ -n "$LOG" ]; then
        echo "Agent log file: $LOG"
        echo "Size: $(ls -lh "$LOG" | awk '{print $5}')"
        INITIAL_EVENTS=$(grep -c 'EVENT RECEIVED' "$LOG" 2>/dev/null || echo 0)
        INITIAL_ANOMALIES=$(grep -c 'ANOMALY DETECTED' "$LOG" 2>/dev/null || echo 0)
        INITIAL_HIGH_RISK=$(grep -c 'HIGH RISK DETECTED' "$LOG" 2>/dev/null || echo 0)
        echo "Initial counts:"
        echo "  Events: $INITIAL_EVENTS"
        echo "  Anomalies: $INITIAL_ANOMALIES"
        echo "  High-Risk: $INITIAL_HIGH_RISK"
    else
        echo "⚠️  No log file found"
        INITIAL_EVENTS=0
        INITIAL_ANOMALIES=0
        INITIAL_HIGH_RISK=0
    fi
    echo ""
    
    # ========================================================================
    # PHASE 2: NORMAL MONITORING (2 minutes)
    # ========================================================================
    echo "======================================================================"
    echo "PHASE 2: NORMAL MONITORING (2 minutes)"
    echo "======================================================================"
    echo ""
    echo "Command: Monitoring normal system activity..."
    echo "Start time: $(date)"
    for i in {1..24}; do
        sleep 5
        if [ -n "$LOG" ]; then
            CURRENT_EVENTS=$(grep -c 'EVENT RECEIVED' "$LOG" 2>/dev/null || echo 0)
            if [ $((i % 6)) -eq 0 ]; then
                echo "[$(date +%H:%M:%S)] Events: $CURRENT_EVENTS"
            fi
        fi
    done
    echo ""
    echo "Normal monitoring complete"
    echo ""
    
    # ========================================================================
    # PHASE 3: ANOMALY DETECTION TEST
    # ========================================================================
    echo "======================================================================"
    echo "PHASE 3: ANOMALY DETECTION TEST"
    echo "======================================================================"
    echo ""
    echo "Command: Running attack simulation to trigger anomalies..."
    echo "Start time: $(date)"
    python3 scripts/simulate_attacks.py 2>&1 | head -30
    echo ""
    echo "Waiting 30 seconds for detection..."
    sleep 30
    echo ""
    
    if [ -n "$LOG" ]; then
        ANOMALIES_AFTER=$(grep -c 'ANOMALY DETECTED' "$LOG" 2>/dev/null || echo 0)
        ANOMALIES_NEW=$((ANOMALIES_AFTER - INITIAL_ANOMALIES))
        echo "Anomaly detection results:"
        echo "  Before: $INITIAL_ANOMALIES"
        echo "  After: $ANOMALIES_AFTER"
        echo "  New detections: $ANOMALIES_NEW"
        echo ""
        
        if [ "$ANOMALIES_NEW" -gt 0 ]; then
            echo "✅ ANOMALY DETECTION WORKING!"
            echo "Recent anomaly detections:"
            grep 'ANOMALY DETECTED' "$LOG" 2>/dev/null | tail -5
        else
            echo "⚠️  No new anomalies detected (may need more aggressive attacks)"
        fi
    fi
    echo ""
    
    # ========================================================================
    # PHASE 4: HIGH-RISK DETECTION TEST
    # ========================================================================
    echo "======================================================================"
    echo "PHASE 4: HIGH-RISK DETECTION TEST"
    echo "======================================================================"
    echo ""
    echo "Command: Running high-risk commands..."
    echo "Start time: $(date)"
    
    # Create test file and run high-risk operations
    touch /tmp/test_security_file
    chmod 777 /tmp/test_security_file
    chown root:root /tmp/test_security_file 2>/dev/null || true
    
    # Run multiple high-risk operations
    for i in {1..5}; do
        chmod 777 /tmp/test_security_file
        sleep 1
    done
    
    echo "High-risk commands executed"
    echo "Waiting 15 seconds for detection..."
    sleep 15
    echo ""
    
    if [ -n "$LOG" ]; then
        HIGH_RISK_AFTER=$(grep -c 'HIGH RISK DETECTED' "$LOG" 2>/dev/null || echo 0)
        HIGH_RISK_NEW=$((HIGH_RISK_AFTER - INITIAL_HIGH_RISK))
        echo "High-risk detection results:"
        echo "  Before: $INITIAL_HIGH_RISK"
        echo "  After: $HIGH_RISK_AFTER"
        echo "  New detections: $HIGH_RISK_NEW"
        echo ""
        
        if [ "$HIGH_RISK_NEW" -gt 0 ]; then
            echo "✅ HIGH-RISK DETECTION WORKING!"
            echo "Recent high-risk detections:"
            grep 'HIGH RISK DETECTED' "$LOG" 2>/dev/null | tail -5
        else
            echo "⚠️  No new high-risk detections"
        fi
    fi
    echo ""
    
    # ========================================================================
    # PHASE 5: PORT SCAN TEST
    # ========================================================================
    echo "======================================================================"
    echo "PHASE 5: PORT SCAN DETECTION TEST"
    echo "======================================================================"
    echo ""
    echo "Command: Running port scan simulation..."
    echo "Start time: $(date)"
    
    python3 -c "
import socket
import time
print('Starting port scan...')
for port in range(8000, 8020):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.1)
        s.connect(('127.0.0.1', port))
        s.close()
    except:
        pass
    time.sleep(0.1)
print('Port scan complete')
"
    
    echo "Waiting 20 seconds for detection..."
    sleep 20
    echo ""
    
    if [ -n "$LOG" ]; then
        PORT_SCANS=$(grep -c 'PORT_SCANNING' "$LOG" 2>/dev/null || echo 0)
        echo "Port scan detection results:"
        echo "  Total port scans detected: $PORT_SCANS"
        echo ""
        
        if [ "$PORT_SCANS" -gt 0 ]; then
            echo "✅ PORT SCAN DETECTION WORKING!"
            echo "Recent port scan detections:"
            grep 'PORT_SCANNING' "$LOG" 2>/dev/null | tail -3
        else
            echo "⚠️  No port scans detected"
        fi
    fi
    echo ""
    
    # ========================================================================
    # PHASE 6: RESPONSE HANDLER TEST (SAFE - WARNINGS ONLY)
    # ========================================================================
    echo "======================================================================"
    echo "PHASE 6: RESPONSE HANDLER TEST (SAFE MODE)"
    echo "======================================================================"
    echo ""
    echo "Command: Checking if response handler is integrated..."
    if grep -q "ResponseHandler\|response_handler" core/simple_agent.py 2>/dev/null; then
        echo "✅ Response handler code found in simple_agent.py"
        
        # Check if it's enabled in config
        if grep -q "enable_responses.*true" config/config.yml 2>/dev/null; then
            echo "⚠️  Response handler is ENABLED in config"
            echo "Checking for response actions in logs..."
            if [ -n "$LOG" ]; then
                RESPONSE_ACTIONS=$(grep -c 'Response action taken\|🛡️' "$LOG" 2>/dev/null || echo 0)
                echo "  Response actions logged: $RESPONSE_ACTIONS"
                if [ "$RESPONSE_ACTIONS" -gt 0 ]; then
                    echo "✅ Response handler is ACTIVE!"
                    grep 'Response action taken\|🛡️' "$LOG" 2>/dev/null | tail -3
                else
                    echo "ℹ️  Response handler integrated but no actions taken (thresholds may be high)"
                fi
            fi
        else
            echo "ℹ️  Response handler is DISABLED (safe mode - as expected)"
        fi
    else
        echo "❌ Response handler not found in code"
    fi
    echo ""
    
    # ========================================================================
    # PHASE 7: FINAL STATUS
    # ========================================================================
    echo "======================================================================"
    echo "PHASE 7: FINAL STATUS & SUMMARY"
    echo "======================================================================"
    echo ""
    echo "Command: Gathering final statistics..."
    
    if [ -n "$LOG" ]; then
        FINAL_EVENTS=$(grep -c 'EVENT RECEIVED' "$LOG" 2>/dev/null || echo 0)
        FINAL_ANOMALIES=$(grep -c 'ANOMALY DETECTED' "$LOG" 2>/dev/null || echo 0)
        FINAL_HIGH_RISK=$(grep -c 'HIGH RISK DETECTED' "$LOG" 2>/dev/null || echo 0)
        FINAL_PORT_SCANS=$(grep -c 'PORT_SCANNING' "$LOG" 2>/dev/null || echo 0)
        
        echo ""
        echo "=== FINAL DETECTION COUNTS ==="
        echo "Total Events: $FINAL_EVENTS"
        echo "Anomalies Detected: $FINAL_ANOMALIES (was $INITIAL_ANOMALIES, +$((FINAL_ANOMALIES - INITIAL_ANOMALIES)))"
        echo "High-Risk Detected: $FINAL_HIGH_RISK (was $INITIAL_HIGH_RISK, +$((FINAL_HIGH_RISK - INITIAL_HIGH_RISK)))"
        echo "Port Scans Detected: $FINAL_PORT_SCANS"
        echo ""
        
        echo "=== VERIFICATION RESULTS ==="
        if [ "$FINAL_ANOMALIES" -gt "$INITIAL_ANOMALIES" ]; then
            echo "✅ Anomaly Detection: WORKING (detected $((FINAL_ANOMALIES - INITIAL_ANOMALIES)) new anomalies)"
        else
            echo "⚠️  Anomaly Detection: No new detections (may need more aggressive attacks or lower thresholds)"
        fi
        
        if [ "$FINAL_HIGH_RISK" -gt "$INITIAL_HIGH_RISK" ]; then
            echo "✅ High-Risk Detection: WORKING (detected $((FINAL_HIGH_RISK - INITIAL_HIGH_RISK)) new high-risk processes)"
        else
            echo "⚠️  High-Risk Detection: No new detections"
        fi
        
        if [ "$FINAL_PORT_SCANS" -gt 0 ]; then
            echo "✅ Port Scan Detection: WORKING ($FINAL_PORT_SCANS detections)"
        else
            echo "⚠️  Port Scan Detection: No detections"
        fi
        
        echo ""
        echo "=== AGENT STATUS ==="
        if ps aux | grep -q '[s]imple_agent'; then
            echo "✅ Agent: RUNNING"
        else
            echo "❌ Agent: NOT RUNNING"
        fi
        
        HTTP_CODE=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:5001 2>/dev/null)
        if [ "$HTTP_CODE" = "200" ]; then
            echo "✅ Dashboard: RUNNING (HTTP $HTTP_CODE)"
        else
            echo "⚠️  Dashboard: HTTP $HTTP_CODE"
        fi
    fi
    echo ""
    
    echo "======================================================================"
    echo "VERIFICATION COMPLETE"
    echo "======================================================================"
    echo "End time: $(date)"
    echo "Log file: $LOG_FILE"
    echo "======================================================================"
    
} 2>&1 | tee "$LOG_FILE"

echo ""
echo "✅ Verification log saved to: $LOG_FILE"
echo "File size: $(ls -lh "$LOG_FILE" | awk '{print $5}')"
echo "Lines: $(wc -l < "$LOG_FILE")"
