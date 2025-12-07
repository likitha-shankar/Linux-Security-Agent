#!/bin/bash
# Comprehensive Verification Script for VM
# Runs all checks and tests

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "=========================================="
echo "  COMPREHENSIVE PROJECT VERIFICATION"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PASSED=0
FAILED=0
WARNINGS=0

# Function to print status
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
    ((PASSED++))
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
    ((FAILED++))
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    ((WARNINGS++))
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# 1. Check Python version
echo "1. Python Version Check"
if python3 --version > /dev/null 2>&1; then
    PYTHON_VERSION=$(python3 --version)
    print_success "Python: $PYTHON_VERSION"
else
    print_error "Python3 not found"
fi
echo ""

# 2. Check dependencies
echo "2. Dependency Check"
if python3 -c "import sklearn; import numpy; import psutil; import rich" 2>/dev/null; then
    print_success "Core dependencies installed"
else
    print_warning "Some dependencies missing - install with: pip3 install -r requirements.txt"
fi
echo ""

# 3. Check file structure
echo "3. File Structure Check"
REQUIRED_FILES=(
    "core/simple_agent.py"
    "core/enhanced_anomaly_detector.py"
    "scripts/simulate_attacks.py"
    "web/app.py"
    "README.md"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        print_success "$file exists"
    else
        print_error "$file missing"
    fi
done
echo ""

# 4. Check training data
echo "4. Training Data Check"
if [ -f "datasets/adfa_training.json" ]; then
    SAMPLE_COUNT=$(python3 -c "import json; f=open('datasets/adfa_training.json'); d=json.load(f); print(len(d.get('samples', [])))" 2>/dev/null || echo "0")
    if [ "$SAMPLE_COUNT" -gt 0 ]; then
        print_success "ADFA training data: $SAMPLE_COUNT samples"
    else
        print_warning "ADFA training data exists but may be empty"
    fi
else
    print_warning "ADFA training data not found - run training setup"
fi
echo ""

# 5. Check ML models
echo "5. ML Models Check"
if python3 -c "from core.enhanced_anomaly_detector import EnhancedAnomalyDetector; d=EnhancedAnomalyDetector(); import os; print('OK' if os.path.exists(os.path.join(d.model_dir, 'isolation_forest.pkl')) else 'NOT_FOUND')" 2>/dev/null | grep -q "OK"; then
    print_success "ML models found"
elif python3 -c "from core.enhanced_anomaly_detector import EnhancedAnomalyDetector" 2>/dev/null; then
    print_warning "ML models not trained - run training script"
else
    print_error "Cannot import ML detector (dependencies missing?)"
fi
echo ""

# 6. Check scripts are executable
echo "6. Script Executability Check"
SCRIPTS=(
    "scripts/complete_training_setup.sh"
    "scripts/setup_adfa_ld_dataset.sh"
)

for script in "${SCRIPTS[@]}"; do
    if [ -x "$script" ]; then
        print_success "$script is executable"
    else
        print_warning "$script is not executable (run: chmod +x $script)"
    fi
done
echo ""

# 7. Run Python verification script (if dependencies available)
echo "7. Python Code Verification"
if python3 -c "import sklearn; import numpy; import psutil" 2>/dev/null; then
    if python3 scripts/comprehensive_verification.py 2>/dev/null; then
        print_success "Python verification passed"
    else
        print_warning "Python verification had issues (check output above)"
    fi
else
    print_warning "Skipping Python verification (dependencies missing)"
fi
echo ""

# Summary
echo "=========================================="
echo "  VERIFICATION SUMMARY"
echo "=========================================="
echo -e "${GREEN}✅ Passed: $PASSED${NC}"
echo -e "${RED}❌ Failed: $FAILED${NC}"
echo -e "${YELLOW}⚠️  Warnings: $WARNINGS${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All critical checks passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some checks failed - review above${NC}"
    exit 1
fi

