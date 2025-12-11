#!/bin/bash
cd ~/Linux-Security-Agent
sudo pkill -9 -f simple_agent.py 2>/dev/null
sleep 2
sudo auditctl -a always,exit -F arch=b64 -S socket -S connect -S execve -S fork -S clone -S setuid -S chmod -S chown -k security_syscalls 2>&1 | grep -v "Rule exists"
sudo nohup python3 core/simple_agent.py --collector auditd --threshold 20 --headless > /tmp/agent.log 2>&1 &
sleep 8
ps aux | grep simple_agent | grep -v grep
