#!/bin/bash
# Complete Training Setup Script
# Converts ADFA-LD dataset and trains models with progress

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "======================================================================"
echo "🧠 COMPLETE ML TRAINING SETUP"
echo "======================================================================"
echo ""

# Change to project root
cd "$PROJECT_ROOT"
echo "📁 Working directory: $(pwd)"
echo ""

# Step 1: Convert ADFA-LD dataset
echo "======================================================================"
echo "STEP 1: Converting ADFA-LD Dataset"
echo "======================================================================"
echo ""

ADFA_DIR="$HOME/datasets/ADFA-LD/ADFA-LD"
OUTPUT_FILE="datasets/adfa_training.json"

# Check if dataset exists
if [ ! -d "$ADFA_DIR" ]; then
    echo "❌ ADFA-LD dataset not found at: $ADFA_DIR"
    echo "   Please run: bash scripts/setup_adfa_ld_dataset.sh first"
    exit 1
fi

echo "📂 Dataset location: $ADFA_DIR"
echo "📝 Output file: $OUTPUT_FILE"
echo ""

# Create datasets directory if it doesn't exist
mkdir -p datasets

# Run conversion
echo "🔄 Converting syscall numbers to names..."
python3 scripts/download_real_datasets.py --adfa-dir "$ADFA_DIR" --output "$OUTPUT_FILE"

if [ ! -f "$OUTPUT_FILE" ]; then
    echo "❌ Conversion failed - output file not created"
    exit 1
fi

echo ""
echo "✅ Conversion complete!"
echo ""

# Step 2: Train models
echo "======================================================================"
echo "STEP 2: Training ML Models"
echo "======================================================================"
echo ""

echo "🧠 Starting model training with real ADFA-LD data..."
echo ""

python3 scripts/train_with_progress.py --file "$OUTPUT_FILE"

echo ""
echo "======================================================================"
echo "✅ TRAINING SETUP COMPLETE!"
echo "======================================================================"
echo ""
echo "📊 Summary:"
echo "   - Dataset: ADFA-LD (real syscall data)"
echo "   - Training file: $OUTPUT_FILE"
echo "   - Models location: ~/.cache/security_agent"
echo ""
echo "🧪 Quick verification:"
python3 -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT')
from core.enhanced_anomaly_detector import EnhancedAnomalyDetector

detector = EnhancedAnomalyDetector()
detector._load_models()

if detector.is_fitted:
    test_syscalls = ['read', 'write', 'open', 'close'] * 10
    result = detector.detect_anomaly_ensemble(
        test_syscalls, 
        {'cpu_percent': 10.0, 'memory_percent': 5.0, 'num_threads': 1}
    )
    print(f'   ✅ Test detection: Score={result.anomaly_score:.2f}, IsAnomaly={result.is_anomaly}')
    print(f'   ✅ Models are working correctly!')
else:
    print('   ❌ Models not loaded properly')
    sys.exit(1)
"

echo ""
echo "🎉 All done! Your agent is ready to use with real trained models."

