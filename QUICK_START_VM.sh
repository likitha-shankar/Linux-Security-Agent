#!/bin/bash
# Quick Start Guide for Linux Security Agent on VM
# VM: instance-20251205-050017 (136.112.137.224)
# Author: Likitha Shankar
# Date: December 2025

set -e  # Exit on error

echo "=================================================="
echo "🚀 Linux Security Agent - VM Quick Start"
echo "=================================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're on the correct VM
echo "📍 Checking VM..."
EXTERNAL_IP=$(curl -s http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip -H "Metadata-Flavor: Google" 2>/dev/null || echo "unknown")
if [ "$EXTERNAL_IP" != "136.112.137.224" ]; then
    echo -e "${YELLOW}⚠️  Warning: Expected VM IP 136.112.137.224, got $EXTERNAL_IP${NC}"
    echo "   (This script is designed for instance-20251205-050017)"
fi

echo ""
echo "=================================================="
echo "📊 Option 1: Run Performance Benchmarks"
echo "=================================================="
echo ""
echo "Quick benchmark (60s): sudo python3 scripts/comprehensive_performance_benchmark.py --quick"
echo "Full benchmark (120s): sudo python3 scripts/comprehensive_performance_benchmark.py"
echo ""
read -p "Run benchmarks now? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${GREEN}✅ Running performance benchmarks...${NC}"
    sudo python3 scripts/comprehensive_performance_benchmark.py --quick
    echo -e "${GREEN}✅ Benchmarks complete! Results saved to docs/reports/performance_benchmark.json${NC}"
fi

echo ""
echo "=================================================="
echo "🤖 Option 2: Evaluate ML Models"
echo "=================================================="
echo ""
echo "1. Train models:        python3 scripts/train_with_dataset.py --file datasets/adfa_training.json"
echo "2. Evaluate models:     python3 scripts/evaluate_ml_models.py"
echo "3. Feature importance:  python3 scripts/analyze_feature_importance.py"
echo ""
read -p "Evaluate ML models now? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${GREEN}✅ Evaluating ML models...${NC}"
    
    # Check if models exist
    if [ ! -f "$HOME/.cache/security_agent/isolation_forest.pkl" ]; then
        echo -e "${YELLOW}⚠️  ML models not found. Training first...${NC}"
        if [ ! -f "datasets/adfa_training.json" ]; then
            echo -e "${RED}❌ Training dataset not found: datasets/adfa_training.json${NC}"
            echo "   Please download ADFA-LD dataset or use: bash scripts/complete_training_setup.sh"
        else
            python3 scripts/train_with_dataset.py --file datasets/adfa_training.json
        fi
    fi
    
    # Evaluate models
    if [ -f "$HOME/.cache/security_agent/isolation_forest.pkl" ]; then
        python3 scripts/evaluate_ml_models.py
        echo -e "${GREEN}✅ ML evaluation complete!${NC}"
    fi
fi

echo ""
echo "=================================================="
echo "🛡️ Option 3: Run Agent Demo"
echo "=================================================="
echo ""
echo "1. Simple agent (recommended): sudo python3 core/simple_agent.py --collector ebpf --dashboard"
echo "2. Enhanced agent (full features): sudo python3 core/enhanced_security_agent.py --dashboard"
echo "3. Web dashboard: python3 web/app.py"
echo ""
read -p "Start agent demo? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${GREEN}✅ Starting agent demo...${NC}"
    
    # Check for auditd rules
    if ! sudo auditctl -l | grep -q "network_syscalls"; then
        echo -e "${YELLOW}⚠️  Auditd rules not configured. Adding network syscall rules...${NC}"
        sudo auditctl -a always,exit -F arch=b64 -S socket -S connect -S bind -S accept -S sendto -S recvfrom -k network_syscalls
        echo -e "${GREEN}✅ Auditd rules configured${NC}"
    fi
    
    # Start agent
    echo -e "${GREEN}🚀 Starting simple agent with eBPF...${NC}"
    echo "   (Press Ctrl+C to stop)"
    sudo python3 core/simple_agent.py --collector ebpf --dashboard --timeout 60
fi

echo ""
echo "=================================================="
echo "🎯 Option 4: Run Attack Simulation"
echo "=================================================="
echo ""
echo "Simulate attacks to test detection: python3 scripts/simulate_attacks.py"
echo ""
read -p "Run attack simulation? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${GREEN}✅ Running attack simulation...${NC}"
    python3 scripts/simulate_attacks.py
    echo -e "${GREEN}✅ Attack simulation complete!${NC}"
fi

echo ""
echo "=================================================="
echo "📚 Documentation Links"
echo "=================================================="
echo ""
echo "📊 Performance Benchmarks:  docs/PERFORMANCE_BENCHMARKS.md"
echo "🤖 ML Evaluation Metrics:   docs/ML_EVALUATION_METRICS.md"
echo "🏭 Production Readiness:    docs/PRODUCTION_READINESS.md"
echo "🔍 Gap Analysis:            docs/GAP_ANALYSIS.md"
echo "✅ Fixes Completed:         docs/FIXES_COMPLETED_DEC_2025.md"
echo ""

echo "=================================================="
echo "🎓 Quick Commands Reference"
echo "=================================================="
echo ""
echo "# Train ML models:"
echo "python3 scripts/train_with_dataset.py --file datasets/adfa_training.json"
echo ""
echo "# Start agent (simple):"
echo "sudo python3 core/simple_agent.py --collector ebpf --dashboard"
echo ""
echo "# Start web dashboard:"
echo "cd web && python3 app.py"
echo ""
echo "# Run attack tests:"
echo "python3 scripts/simulate_attacks.py"
echo ""
echo "# Run benchmarks:"
echo "sudo python3 scripts/comprehensive_performance_benchmark.py --quick"
echo ""
echo "# Evaluate ML models:"
echo "python3 scripts/evaluate_ml_models.py"
echo ""

echo "=================================================="
echo "✅ Quick Start Complete!"
echo "=================================================="
echo ""
echo "Your VM is ready for demonstration!"
echo ""
echo -e "${GREEN}External IP: $EXTERNAL_IP${NC}"
echo -e "${GREEN}SSH: ssh <user>@$EXTERNAL_IP${NC}"
echo -e "${GREEN}Web Dashboard: http://localhost:5001 (port forward: ssh -L 5001:localhost:5001 <user>@$EXTERNAL_IP)${NC}"
echo ""

# Create a symlink for easy access
if [ ! -L "$HOME/quickstart.sh" ]; then
    ln -s "$(pwd)/QUICK_START_VM.sh" "$HOME/quickstart.sh"
    echo -e "${GREEN}✅ Created shortcut: ~/quickstart.sh${NC}"
fi

echo ""
echo "Run this script again anytime: bash QUICK_START_VM.sh"
echo "Or use shortcut: bash ~/quickstart.sh"
echo ""
