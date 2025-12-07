#!/bin/bash
# Generate realistic training data and train models with progress

set -e

echo "======================================================================"
echo "GENERATE REALISTIC TRAINING DATA AND TRAIN MODELS"
echo "======================================================================"

# Step 1: Generate realistic training data
echo ""
echo "Step 1: Generating realistic training data (900 samples)..."
python3 scripts/create_realistic_training_data.py --samples 150

if [ ! -f "datasets/realistic_training_data.json" ]; then
    echo "❌ Failed to generate training data"
    exit 1
fi

echo ""
echo "Step 2: Training ML models with detailed progress..."
python3 scripts/train_with_progress.py --file datasets/realistic_training_data.json

echo ""
echo "======================================================================"
echo "✅ COMPLETE!"
echo "======================================================================"
echo ""
echo "Next steps:"
echo "  1. Verify models: python3 scripts/verify_ml_implementation.py"
echo "  2. Test agent: sudo python3 core/simple_agent.py --collector ebpf"
echo ""

