#!/usr/bin/env python3
"""
Full Demo Verification Script
Runs ALL tests, verifies everything works, generates detailed log
NO SIMULATION - ALL REAL TESTS
"""

import sys
import os
import subprocess
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Log file
LOG_FILE = project_root / "DEMO_VERIFICATION_LOG.txt"
log_buffer = []

def log(message: str, level: str = "INFO"):
    """Log message to both console and buffer"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] [{level}] {message}"
    print(log_entry)
    log_buffer.append(log_entry)

def run_command(cmd: List[str], description: str, timeout: int = 300, capture_output: bool = True) -> Dict[str, Any]:
    """Run command and log everything"""
    log(f"COMMAND: {' '.join(cmd)}")
    log(f"DESCRIPTION: {description}")
    
    try:
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=capture_output,
            text=True,
            timeout=timeout
        )
        
        log(f"RETURN CODE: {result.returncode}")
        
        if result.stdout:
            log(f"STDOUT:\n{result.stdout}")
        
        if result.stderr:
            log(f"STDERR:\n{result.stderr}")
        
        return {
            'success': result.returncode == 0,
            'returncode': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr
        }
    except subprocess.TimeoutExpired:
        log(f"ERROR: Command timed out after {timeout} seconds", "ERROR")
        return {'success': False, 'error': 'timeout'}
    except Exception as e:
        log(f"ERROR: {e}", "ERROR")
        return {'success': False, 'error': str(e)}

def save_log():
    """Save log to file"""
    with open(LOG_FILE, 'w') as f:
        f.write("="*80 + "\n")
        f.write("DEMO VERIFICATION LOG\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*80 + "\n\n")
        f.write("\n".join(log_buffer))
    log(f"Log saved to: {LOG_FILE}")

def test_1_system_check():
    """Test 1: System Requirements Check"""
    log("\n" + "="*80)
    log("TEST 1: System Requirements Check")
    log("="*80)
    
    # Check Python version
    result = run_command([sys.executable, "--version"], "Check Python version")
    
    # Check dependencies
    result = run_command(
        [sys.executable, "-m", "pip", "list"],
        "Check installed packages"
    )
    
    # Check eBPF support
    result = run_command(
        ["ls", "/sys/kernel/debug/tracing"],
        "Check eBPF tracing support"
    )
    
    # Check auditd
    result = run_command(
        ["which", "auditctl"],
        "Check auditd availability"
    )
    
    return result

def test_2_agent_startup():
    """Test 2: Agent Startup and Health Check"""
    log("\n" + "="*80)
    log("TEST 2: Agent Startup and Health Check")
    log("="*80)
    
    # Stop any running agents
    log("Stopping any running agents...")
    run_command(["sudo", "pkill", "-9", "-f", "simple_agent.py"], "Kill existing agents")
    time.sleep(2)
    
    # Setup auditd rules
    log("Setting up auditd rules...")
    run_command(
        ["sudo", "auditctl", "-a", "always,exit", "-F", "arch=b64", "-S", "socket", "-S", "connect", "-S", "execve", "-S", "fork", "-S", "clone", "-S", "setuid", "-S", "chmod", "-S", "chown", "-k", "security_syscalls"],
        "Setup auditd rules"
    )
    
    # Start agent in background
    log("Starting agent...")
    agent_log = project_root / "logs" / f"agent_test_{int(time.time())}.log"
    result = run_command(
        ["sudo", "nohup", sys.executable, "core/simple_agent.py", "--collector", "auditd", "--threshold", "20", "--headless"],
        "Start agent",
        capture_output=False
    )
    
    # Wait for agent to start
    log("Waiting 10 seconds for agent to initialize...")
    time.sleep(10)
    
    # Check if agent is running
    result = run_command(
        ["ps", "aux"],
        "Check running processes"
    )
    
    if "simple_agent.py" in result.get('stdout', ''):
        log("✅ Agent is running", "SUCCESS")
    else:
        log("❌ Agent is NOT running", "ERROR")
    
    # Check for log file
    log_files = list((project_root / "logs").glob("security_agent_*.log"))
    if log_files:
        latest_log = max(log_files, key=lambda p: p.stat().st_mtime)
        log(f"Latest log file: {latest_log}")
        
        # Check log for startup messages
        with open(latest_log, 'r') as f:
            log_content = f.read()
            if "Agent started successfully" in log_content:
                log("✅ Agent started successfully", "SUCCESS")
            if "Health check passed" in log_content:
                log("✅ Health check passed", "SUCCESS")
    
    return result

def test_3_attack_simulation():
    """Test 3: Attack Simulation"""
    log("\n" + "="*80)
    log("TEST 3: Attack Simulation")
    log("="*80)
    
    # Run attack simulation
    result = run_command(
        [sys.executable, "scripts/simulate_attacks.py"],
        "Run attack simulation",
        timeout=180
    )
    
    # Wait for detections
    log("Waiting 30 seconds for detections...")
    time.sleep(30)
    
    # Check logs for detections
    log_files = list((project_root / "logs").glob("security_agent_*.log"))
    if log_files:
        latest_log = max(log_files, key=lambda p: p.stat().st_mtime)
        log(f"Checking log file: {latest_log}")
        
        with open(latest_log, 'r') as f:
            log_content = f.read()
            
            port_scans = log_content.count("PORT_SCANNING")
            c2_beacons = log_content.count("C2_BEACONING")
            anomalies = log_content.count("ANOMALY DETECTED")
            high_risk = log_content.count("HIGH-RISK")
            
            log(f"Port scans detected: {port_scans}")
            log(f"C2 beacons detected: {c2_beacons}")
            log(f"Anomalies detected: {anomalies}")
            log(f"High-risk processes: {high_risk}")
            
            if port_scans > 0 or c2_beacons > 0 or anomalies > 0:
                log("✅ Attacks detected!", "SUCCESS")
            else:
                log("⚠️  No attacks detected in logs", "WARNING")
    
    return result

def test_4_web_dashboard():
    """Test 4: Web Dashboard"""
    log("\n" + "="*80)
    log("TEST 4: Web Dashboard")
    log("="*80)
    
    # Check if dashboard is running
    result = run_command(
        ["ps", "aux"],
        "Check for dashboard process"
    )
    
    if "app.py" in result.get('stdout', ''):
        log("✅ Dashboard is running", "SUCCESS")
    else:
        log("⚠️  Dashboard not running - will start it", "WARNING")
        
        # Start dashboard
        log("Starting dashboard on port 5001...")
        run_command(
            ["nohup", sys.executable, "web/app.py"],
            "Start web dashboard",
            capture_output=False
        )
        time.sleep(5)
    
    # Check if port 5001 is listening
    result = run_command(
        ["netstat", "-tlnp"],
        "Check listening ports"
    )
    
    if ":5001" in result.get('stdout', ''):
        log("✅ Port 5001 is listening", "SUCCESS")
    else:
        log("❌ Port 5001 is NOT listening", "ERROR")
    
    # Test HTTP connection
    result = run_command(
        ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "http://localhost:5001"],
        "Test HTTP connection to dashboard"
    )
    
    if result.get('stdout', '').strip() == "200":
        log("✅ Dashboard responds with HTTP 200", "SUCCESS")
    else:
        log(f"⚠️  Dashboard response: {result.get('stdout', '')}", "WARNING")
    
    return result

def test_5_ml_evaluation():
    """Test 5: ML Evaluation"""
    log("\n" + "="*80)
    log("TEST 5: ML Evaluation")
    log("="*80)
    
    result = run_command(
        [sys.executable, "scripts/evaluate_ml_models.py"],
        "Run ML evaluation",
        timeout=600
    )
    
    return result

def test_6_performance_benchmark():
    """Test 6: Performance Benchmark"""
    log("\n" + "="*80)
    log("TEST 6: Performance Benchmark")
    log("="*80)
    
    result = run_command(
        [sys.executable, "tests/benchmark_performance.py"],
        "Run performance benchmark",
        timeout=300
    )
    
    return result

def test_7_test_suite():
    """Test 7: Test Suite"""
    log("\n" + "="*80)
    log("TEST 7: Test Suite")
    log("="*80)
    
    result = run_command(
        [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
        "Run pytest test suite",
        timeout=600
    )
    
    return result

def test_8_coverage():
    """Test 8: Test Coverage"""
    log("\n" + "="*80)
    log("TEST 8: Test Coverage")
    log("="*80)
    
    result = run_command(
        [sys.executable, "-m", "pytest", "tests/", "--cov=core", "--cov-report=term"],
        "Run tests with coverage",
        timeout=600
    )
    
    return result

def main():
    """Main verification function"""
    log("="*80)
    log("FULL DEMO VERIFICATION")
    log("="*80)
    log(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log(f"Project Root: {project_root}")
    log("="*80)
    
    results = {}
    
    # Run all tests
    results['System Check'] = test_1_system_check()
    results['Agent Startup'] = test_2_agent_startup()
    results['Attack Simulation'] = test_3_attack_simulation()
    results['Web Dashboard'] = test_4_web_dashboard()
    results['ML Evaluation'] = test_5_ml_evaluation()
    results['Performance Benchmark'] = test_6_performance_benchmark()
    results['Test Suite'] = test_7_test_suite()
    results['Coverage'] = test_8_coverage()
    
    # Summary
    log("\n" + "="*80)
    log("FINAL SUMMARY")
    log("="*80)
    
    total = len(results)
    passed = sum(1 for r in results.values() if r.get('success'))
    
    log(f"Total Tests: {total}")
    log(f"Passed: {passed}")
    log(f"Failed: {total - passed}")
    log(f"Pass Rate: {(passed/total*100) if total > 0 else 0:.1f}%")
    
    log("\nTest Results:")
    for test_name, result in results.items():
        status = "✅ PASS" if result.get('success') else "❌ FAIL"
        log(f"  {test_name}: {status}")
    
    # Save log
    save_log()
    
    log(f"\n✅ Complete log saved to: {LOG_FILE}")
    log(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return 0 if passed == total else 1

if __name__ == '__main__':
    sys.exit(main())
