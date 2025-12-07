#!/usr/bin/env python3
"""
Diagnostic script to identify agent issues
Run this to check what's wrong with the agent
"""

import os
import sys
import subprocess
import time
from pathlib import Path

# Colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(text):
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}{text}{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")

def check_file_exists(path, description):
    """Check if file exists"""
    p = Path(path)
    if p.exists():
        print(f"{GREEN}✅{RESET} {description}: {path}")
        if p.is_file():
            size = p.stat().st_size
            mtime = time.ctime(p.stat().st_mtime)
            print(f"   Size: {size} bytes | Modified: {mtime}")
        return True
    else:
        print(f"{RED}❌{RESET} {description}: {path} (NOT FOUND)")
        return False

def check_process_running(pattern):
    """Check if process is running"""
    try:
        result = subprocess.run(['pgrep', '-f', pattern], 
                              capture_output=True, text=True, timeout=2)
        if result.returncode == 0 and result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            print(f"{GREEN}✅{RESET} Process '{pattern}' is running (PIDs: {', '.join(pids)})")
            return True
        else:
            print(f"{YELLOW}⚠️{RESET} Process '{pattern}' is NOT running")
            return False
    except Exception as e:
        print(f"{RED}❌{RESET} Error checking process: {e}")
        return False

def check_log_file(log_path):
    """Check log file content"""
    if not Path(log_path).exists():
        print(f"{RED}❌{RESET} Log file doesn't exist: {log_path}")
        return
    
    print(f"\n{BLUE}📋 Log File Analysis:{RESET}")
    print(f"   Path: {log_path}")
    
    try:
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            total_lines = len(lines)
            print(f"   Total lines: {total_lines}")
            
            if total_lines == 0:
                print(f"{RED}❌{RESET} Log file is empty!")
                return
            
            # Check last 20 lines
            print(f"\n   {YELLOW}Last 20 lines:{RESET}")
            for line in lines[-20:]:
                line = line.strip()
                if line:
                    # Color code by type
                    if 'ERROR' in line or '❌' in line:
                        print(f"   {RED}{line[:100]}{RESET}")
                    elif 'WARNING' in line or '⚠️' in line:
                        print(f"   {YELLOW}{line[:100]}{RESET}")
                    elif 'HIGH RISK' in line or '🔴' in line:
                        print(f"   {RED}🔴 {line[:100]}{RESET}")
                    elif 'ANOMALY DETECTED' in line:
                        print(f"   {YELLOW}⚠️ {line[:100]}{RESET}")
                    elif 'SCORE UPDATE' in line:
                        print(f"   {GREEN}📊 {line[:100]}{RESET}")
                    else:
                        print(f"   {line[:100]}")
            
            # Count different log types
            errors = sum(1 for line in lines if 'ERROR' in line or '❌' in line)
            warnings = sum(1 for line in lines if 'WARNING' in line or '⚠️' in line)
            high_risk = sum(1 for line in lines if 'HIGH RISK' in line or '🔴' in line)
            anomalies = sum(1 for line in lines if 'ANOMALY DETECTED' in line)
            score_updates = sum(1 for line in lines if 'SCORE UPDATE' in line)
            
            print(f"\n   {BLUE}Log Statistics:{RESET}")
            print(f"   Errors: {errors}")
            print(f"   Warnings: {warnings}")
            print(f"   High Risk: {high_risk}")
            print(f"   Anomalies: {anomalies}")
            print(f"   Score Updates: {score_updates}")
            
            # Check for excluded processes being detected
            excluded_in_logs = []
            for line in lines[-100:]:  # Check last 100 lines
                if 'sudo' in line.lower() and ('ANOMALY' in line or 'HIGH RISK' in line):
                    excluded_in_logs.append('sudo')
                if 'sshd' in line.lower() and ('ANOMALY' in line or 'HIGH RISK' in line):
                    excluded_in_logs.append('sshd')
            
            if excluded_in_logs:
                print(f"\n   {RED}⚠️ Excluded processes still being detected: {set(excluded_in_logs)}{RESET}")
            
    except Exception as e:
        print(f"{RED}❌{RESET} Error reading log file: {e}")

def check_web_dashboard():
    """Check web dashboard status"""
    print(f"\n{BLUE}🌐 Web Dashboard Check:{RESET}")
    
    # Check if dashboard is running
    dashboard_running = check_process_running('app.py')
    
    # Check dashboard database
    db_path = Path(__file__).parent.parent / 'web' / 'dashboard.db'
    if db_path.exists():
        print(f"{GREEN}✅{RESET} Dashboard database exists: {db_path}")
    else:
        print(f"{YELLOW}⚠️{RESET} Dashboard database doesn't exist (will be created on first run)")
    
    # Check if port 5001 is in use
    try:
        result = subprocess.run(['netstat', '-tuln'], 
                              capture_output=True, text=True, timeout=2)
        if '5001' in result.stdout:
            print(f"{GREEN}✅{RESET} Port 5001 is in use (dashboard likely running)")
        else:
            print(f"{YELLOW}⚠️{RESET} Port 5001 is not in use (dashboard not running)")
    except:
        try:
            result = subprocess.run(['ss', '-tuln'], 
                                  capture_output=True, text=True, timeout=2)
            if '5001' in result.stdout:
                print(f"{GREEN}✅{RESET} Port 5001 is in use (dashboard likely running)")
            else:
                print(f"{YELLOW}⚠️{RESET} Port 5001 is not in use (dashboard not running)")
        except:
            print(f"{YELLOW}⚠️{RESET} Could not check port status")

def main():
    print_header("Linux Security Agent - Diagnostic Tool")
    
    project_root = Path(__file__).parent.parent
    
    # 1. Check project structure
    print(f"{BLUE}📁 Project Structure:{RESET}")
    check_file_exists(project_root / 'core' / 'simple_agent.py', 'Main agent file')
    check_file_exists(project_root / 'logs', 'Logs directory')
    check_file_exists(project_root / 'web' / 'app.py', 'Web dashboard')
    
    # 2. Check log file
    log_file = project_root / 'logs' / 'security_agent.log'
    log_exists = check_file_exists(log_file, 'Log file')
    
    if log_exists:
        check_log_file(log_file)
    
    # 3. Check if agent is running
    print(f"\n{BLUE}🔄 Process Status:{RESET}")
    agent_running = check_process_running('simple_agent.py')
    
    # 4. Check web dashboard
    check_web_dashboard()
    
    # 5. Check recent activity
    if log_exists and agent_running:
        print(f"\n{BLUE}⏱️  Recent Activity Check:{RESET}")
        try:
            mtime = Path(log_file).stat().st_mtime
            age = time.time() - mtime
            if age < 10:
                print(f"{GREEN}✅{RESET} Log file updated {age:.1f} seconds ago (agent is active)")
            elif age < 60:
                print(f"{YELLOW}⚠️{RESET} Log file updated {age:.1f} seconds ago (agent may be idle)")
            else:
                print(f"{RED}❌{RESET} Log file updated {age:.1f} seconds ago (agent may be stuck)")
        except Exception as e:
            print(f"{RED}❌{RESET} Error checking log age: {e}")
    
    # 6. Recommendations
    print(f"\n{BLUE}💡 Recommendations:{RESET}")
    
    if not agent_running:
        print(f"   1. Start the agent: sudo python3 core/simple_agent.py --collector ebpf --threshold 20")
    
    if not log_exists:
        print(f"   2. Log file doesn't exist - agent hasn't run yet")
    
    if agent_running and log_exists:
        print(f"   3. Agent is running - check logs above for issues")
        print(f"   4. If dashboard shows nothing, restart dashboard: cd web && python3 app.py")
        print(f"   5. If too many false positives, increase threshold: --threshold 30")
    
    print(f"\n{BLUE}{'='*70}{RESET}\n")

if __name__ == '__main__':
    main()

