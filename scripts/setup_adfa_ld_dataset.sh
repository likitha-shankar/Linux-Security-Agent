#!/bin/bash
# Setup ADFA-LD Dataset
# Downloads and prepares ADFA-LD dataset for training

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DATASET_DIR="$HOME/datasets/ADFA-LD"
ADFA_EXTRACTED_DIR="$DATASET_DIR/ADFA-LD"

echo "======================================================================"
echo "ADFA-LD Dataset Setup"
echo "======================================================================"

# Check if dataset already exists
if [ -d "$ADFA_EXTRACTED_DIR" ] && [ -d "$ADFA_EXTRACTED_DIR/Training_Data_Master" ]; then
    echo "✅ ADFA-LD dataset already exists at: $ADFA_EXTRACTED_DIR"
    echo "📂 Dataset structure:"
    ls -la "$ADFA_EXTRACTED_DIR" | head -10
    exit 0
fi

# Create dataset directory
mkdir -p "$DATASET_DIR"
cd "$DATASET_DIR"

echo "📥 Downloading ADFA-LD dataset from GitHub..."

# Try to clone the repository
if [ -d "a-labelled-version-of-the-ADFA-LD-dataset" ]; then
    echo "   Repository directory exists, updating..."
    cd a-labelled-version-of-the-ADFA-LD-dataset
    git pull || true
else
    echo "   Cloning repository..."
    git clone https://github.com/verazuo/a-labelled-version-of-the-ADFA-LD-dataset.git
    cd a-labelled-version-of-the-ADFA-LD-dataset
fi

# Check if zip file exists
if [ -f "ADFA-LD.zip" ]; then
    echo "✅ Found ADFA-LD.zip"
    
    # Extract if not already extracted
    if [ ! -d "ADFA-LD" ]; then
        echo "📦 Extracting ADFA-LD.zip (using Python)..."
        python3 -c "
import zipfile
import sys
try:
    with zipfile.ZipFile('ADFA-LD.zip', 'r') as zip_ref:
        zip_ref.extractall('.')
    print('✅ Extraction complete')
except Exception as e:
    print(f'❌ Extraction failed: {e}')
    sys.exit(1)
"
    else
        echo "✅ ADFA-LD directory already extracted"
    fi
    
    # Move to expected location
    if [ -d "ADFA-LD" ] && [ ! -d "$ADFA_EXTRACTED_DIR" ]; then
        echo "📁 Moving dataset to expected location..."
        mv ADFA-LD "$ADFA_EXTRACTED_DIR"
    fi
else
    echo "❌ ADFA-LD.zip not found in repository"
    echo "   Please check: https://github.com/verazuo/a-labelled-version-of-the-ADFA-LD-dataset"
    exit 1
fi

# Verify dataset structure
if [ -d "$ADFA_EXTRACTED_DIR/Training_Data_Master" ]; then
    echo ""
    echo "✅ Dataset setup complete!"
    echo "📁 Location: $ADFA_EXTRACTED_DIR"
    echo "📊 Dataset structure:"
    echo "   - Training_Data_Master: $(ls -1 "$ADFA_EXTRACTED_DIR/Training_Data_Master" | wc -l) files"
    echo "   - Validation_Data_Master: $(ls -1 "$ADFA_EXTRACTED_DIR/Validation_Data_Master" 2>/dev/null | wc -l || echo 0) files"
    echo "   - Attack_Data_Master: $(ls -1 "$ADFA_EXTRACTED_DIR/Attack_Data_Master" 2>/dev/null | wc -l || echo 0) files"
    echo ""
    echo "📝 Next step:"
    echo "   cd $PROJECT_ROOT"
    echo "   python3 scripts/download_real_datasets.py --adfa-dir $ADFA_EXTRACTED_DIR --output datasets/adfa_training.json"
else
    echo "❌ Dataset structure incomplete. Expected Training_Data_Master directory not found."
    exit 1
fi

