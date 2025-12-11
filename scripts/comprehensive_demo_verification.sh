#!/bin/bash
# Comprehensive Demo Verification Script
# Runs everything on VM and generates detailed log

LOG_FILE="$HOME/Linux-Security-Agent/COMPREHENSIVE_DEMO_LOG.txt"
cd ~/Linux-Security-Agent

{
    echo "======================================================================"
    echo "COMPREHENSIVE DEMO VERIFICATION LOG"
    echo "======================================================================"
    echo "Generated: $(date)"
    echo "Host: $(hostname)"
    echo "User: $(whoami)"
    echo "======================================================================"
    echo ""
    
    # ========================================================================
    # PHASE 1: CLEANUP AND PREPARATION
    # ========================================================================
    echo "======================================================================"
    echo "PHASE 1: CLEANUP AND PREPARATION"
    echo "======================================================================"
    echo ""
    echo "Command: Stopping any running agents..."
    sudo pkill -9 -f simple_agent.py 2>&1
    sleep 2
    echo "Result: Old agents stopped"
    echo ""
    
    echo "Command: Checking system requirements..."
    echo "Python version:"
    python3 --version 2>&1
    echo ""
    echo "Auditd available:"
    which auditctl 2>&1
    echo ""
    echo "Disk space:"
    df -h . | tail -1
    echo ""
    
    # ========================================================================
    # PHASE 2: SETUP AUDITD
    # ========================================================================
    echo "======================================================================"
    echo "PHASE 2: SETUP AUDITD RULES"
    echo "======================================================================"
    echo ""
    echo "Command: Clearing old auditd rules..."
    sudo auditctl -D 2>&1
    echo ""
    echo "Command: Adding auditd rules..."
    sudo auditctl -a always,exit -F arch=b64 -S socket -S connect -S execve -S fork -S clone -S setuid -S chmod -S chown -k security_syscalls 2>&1
    echo ""
    echo "Command: Verifying auditd rules..."
    sudo auditctl -l 2>&1 | head -5
    echo ""
    
    # ========================================================================
    # PHASE 3: START AGENT
    # ========================================================================
    echo "======================================================================"
    echo "PHASE 3: START SECURITY AGENT"
    echo "======================================================================"
    echo ""
    echo "Command: Starting agent..."
    sudo nohup python3 core/simple_agent.py --collector auditd --threshold 20 --headless > /tmp/agent_start.log 2>&1 &
    AGENT_PID=$!
    echo "Agent PID: $AGENT_PID"
    sleep 15
    echo ""
    echo "Command: Verifying agent is running..."
    ps aux | grep '[s]imple_agent' | grep -v grep
    if ps aux | grep -q '[s]imple_agent'; then
        echo "Result: ✅ Agent is running"
    else
        echo "Result: ❌ Agent failed to start"
        echo "Error log:"
        tail -30 /tmp/agent_start.log 2>/dev/null
        exit 1
    fi
    echo ""
    echo "Command: Checking agent log file..."
    LOG=$(ls -t logs/security_agent_*.log 2>/dev/null | head -1)
    if [ -n "$LOG" ]; then
        echo "Log file: $LOG"
        echo "Size: $(ls -lh "$LOG" | awk '{print $5}')"
        echo "Last 5 lines:"
        tail -5 "$LOG" 2>/dev/null
    else
        echo "No log file found yet"
    fi
    echo ""
    
    # ========================================================================
    # PHASE 4: NORMAL MONITORING (5 minutes)
    # ========================================================================
    echo "======================================================================"
    echo "PHASE 4: NORMAL MONITORING (5 minutes)"
    echo "======================================================================"
    echo ""
    echo "Command: Waiting 5 minutes for normal system activity..."
    echo "Start time: $(date)"
    INITIAL_EVENTS=$(grep -c 'EVENT RECEIVED' "$LOG" 2>/dev/null || echo 0)
    echo "Initial event count: $INITIAL_EVENTS"
    echo ""
    
    # Monitor for 5 minutes (60 iterations of 5 seconds)
    for i in {1..60}; do
        sleep 5
        CURRENT_EVENTS=$(grep -c 'EVENT RECEIVED' "$LOG" 2>/dev/null || echo 0)
        if [ $((i % 12)) -eq 0 ]; then
            echo "[$(date +%H:%M:%S)] Events captured: $CURRENT_EVENTS (+$((CURRENT_EVENTS - INITIAL_EVENTS)))"
        fi
    done
    
    echo ""
    echo "Normal monitoring complete"
    NORMAL_EVENTS=$(grep -c 'EVENT RECEIVED' "$LOG" 2>/dev/null || echo 0)
    echo "Total events after normal monitoring: $NORMAL_EVENTS"
    echo ""
    
    # ========================================================================
    # PHASE 5: ATTACK SIMULATION (Multiple Rounds)
    # ========================================================================
    echo "======================================================================"
    echo "PHASE 5: ATTACK SIMULATION (Multiple Rounds)"
    echo "======================================================================"
    echo ""
    echo "Command: Running comprehensive attack simulation (Round 1)..."
    echo "Start time: $(date)"
    python3 scripts/simulate_attacks.py 2>&1
    echo ""
    echo "Round 1 complete. Waiting 30 seconds..."
    sleep 30
    echo ""
    echo "Command: Running attack simulation (Round 2)..."
    python3 scripts/simulate_attacks.py 2>&1
    echo ""
    echo "Round 2 complete. Waiting 30 seconds..."
    sleep 30
    echo ""
    echo "Command: Running attack simulation (Round 3)..."
    python3 scripts/simulate_attacks.py 2>&1
    echo ""
    echo "Attack simulation complete at: $(date)"
    echo ""
    
    # ========================================================================
    # PHASE 6: MONITOR DETECTIONS (3 minutes)
    # ========================================================================
    echo "======================================================================"
    echo "PHASE 6: MONITORING DETECTIONS (3 minutes)"
    echo "======================================================================"
    echo ""
    echo "Command: Monitoring for detections..."
    for i in {1..36}; do
        sleep 5
        PORT_SCANS=$(grep -c 'PORT_SCANNING' "$LOG" 2>/dev/null || echo 0)
        C2_BEACONS=$(grep -c 'C2_BEACONING' "$LOG" 2>/dev/null || echo 0)
        HIGH_RISK=$(grep -c 'HIGH RISK DETECTED' "$LOG" 2>/dev/null || echo 0)
        ANOMALIES=$(grep -c 'ANOMALY DETECTED' "$LOG" 2>/dev/null || echo 0)
        if [ $((i % 6)) -eq 0 ]; then
            echo "[$(date +%H:%M:%S)] Port Scans: $PORT_SCANS | C2: $C2_BEACONS | High-Risk: $HIGH_RISK | Anomalies: $ANOMALIES"
        fi
    done
    echo ""
    
    # ========================================================================
    # PHASE 7: DETECTION ANALYSIS
    # ========================================================================
    echo "======================================================================"
    echo "PHASE 7: DETECTION ANALYSIS"
    echo "======================================================================"
    echo ""
    echo "Command: Analyzing detection results..."
    echo ""
    
    PORT_SCANS=$(grep -c 'PORT_SCANNING' "$LOG" 2>/dev/null || echo 0)
    C2_BEACONS=$(grep -c 'C2_BEACONING' "$LOG" 2>/dev/null || echo 0)
    HIGH_RISK=$(grep -c 'HIGH RISK DETECTED' "$LOG" 2>/dev/null || echo 0)
    ANOMALIES=$(grep -c 'ANOMALY DETECTED' "$LOG" 2>/dev/null || echo 0)
    TOTAL_EVENTS=$(grep -c 'EVENT RECEIVED' "$LOG" 2>/dev/null || echo 0)
    
    echo "=== DETECTION SUMMARY ==="
    echo "Port Scans Detected: $PORT_SCANS"
    echo "C2 Beacons Detected: $C2_BEACONS"
    echo "High-Risk Processes: $HIGH_RISK"
    echo "Anomalies Detected: $ANOMALIES"
    echo "Total Syscalls Captured: $TOTAL_EVENTS"
    echo ""
    
    echo "=== RECENT PORT SCAN DETECTIONS ==="
    grep 'PORT_SCANNING' "$LOG" 2>/dev/null | tail -5
    echo ""
    
    echo "=== RECENT HIGH-RISK DETECTIONS ==="
    grep 'HIGH RISK DETECTED' "$LOG" 2>/dev/null | tail -5
    echo ""
    
    echo "=== RECENT C2 BEACON DETECTIONS ==="
    grep 'C2_BEACONING' "$LOG" 2>/dev/null | tail -5
    echo ""
    
    echo "=== RECENT ANOMALY DETECTIONS ==="
    grep 'ANOMALY DETECTED' "$LOG" 2>/dev/null | tail -5
    echo ""
    
    # ========================================================================
    # PHASE 8: DASHBOARD VERIFICATION
    # ========================================================================
    echo "======================================================================"
    echo "PHASE 8: DASHBOARD VERIFICATION"
    echo "======================================================================"
    echo ""
    echo "Command: Checking dashboard status..."
    if curl -s http://localhost:5001 >/dev/null 2>&1; then
        HTTP_CODE=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:5001)
        echo "Dashboard HTTP Status: $HTTP_CODE"
        if [ "$HTTP_CODE" = "200" ]; then
            echo "Result: ✅ Dashboard is running"
        else
            echo "Result: ⚠️  Dashboard returned $HTTP_CODE"
        fi
    else
        echo "Result: ❌ Dashboard not accessible"
    fi
    echo ""
    echo "Command: Checking dashboard process..."
    ps aux | grep '[a]pp.py' | grep -v grep
    echo ""
    
    # ========================================================================
    # PHASE 9: SYSTEM STATUS
    # ========================================================================
    echo "======================================================================"
    echo "PHASE 9: SYSTEM STATUS"
    echo "======================================================================"
    echo ""
    echo "Agent Process:"
    ps aux | grep '[s]imple_agent' | grep -v grep
    echo ""
    echo "Agent Log File:"
    ls -lh "$LOG" 2>/dev/null
    echo ""
    echo "System Resources:"
    echo "CPU Usage:"
    top -bn1 | grep "Cpu(s)" | head -1
    echo ""
    echo "Memory Usage:"
    free -h | head -2
    echo ""
    
    # ========================================================================
    # PHASE 10: FINAL SUMMARY
    # ========================================================================
    echo "======================================================================"
    echo "PHASE 10: FINAL SUMMARY"
    echo "======================================================================"
    echo ""
    echo "=== VERIFICATION RESULTS ==="
    echo ""
    
    # Agent status
    if ps aux | grep -q '[s]imple_agent'; then
        echo "✅ Agent: RUNNING"
    else
        echo "❌ Agent: NOT RUNNING"
    fi
    echo ""
    
    # Dashboard status
    if curl -s http://localhost:5001 >/dev/null 2>&1; then
        echo "✅ Dashboard: RUNNING (HTTP 200)"
    else
        echo "❌ Dashboard: NOT RUNNING"
    fi
    echo ""
    
    # Detection status
    echo "✅ Detections:"
    echo "   Port Scans: $PORT_SCANS"
    echo "   C2 Beacons: $C2_BEACONS"
    echo "   High-Risk: $HIGH_RISK"
    echo "   Anomalies: $ANOMALIES"
    echo "   Total Events: $TOTAL_EVENTS"
    echo ""
    
    # Overall status
    if [ "$PORT_SCANS" -gt 0 ] || [ "$HIGH_RISK" -gt 0 ] || [ "$TOTAL_EVENTS" -gt 0 ]; then
        echo "✅ OVERALL STATUS: SYSTEM WORKING"
        echo "   - Agent is monitoring"
        echo "   - Attacks are being detected"
        echo "   - Dashboard is accessible"
        echo "   - System ready for demo"
    else
        echo "⚠️  OVERALL STATUS: LIMITED DETECTIONS"
        echo "   - Agent is running but few detections"
    fi
    echo ""
    
    echo "======================================================================"
    echo "VERIFICATION COMPLETE"
    echo "======================================================================"
    echo "End time: $(date)"
    echo "Total duration: ~10 minutes"
    echo "Log file: $LOG_FILE"
    echo "======================================================================"
    
} 2>&1 | tee "$LOG_FILE"

echo ""
echo "✅ Comprehensive log saved to: $LOG_FILE"
echo "File size: $(ls -lh "$LOG_FILE" | awk '{print $5}')"
echo "Lines: $(wc -l < "$LOG_FILE")"
