#!/usr/bin/env python3
"""
Train Models with Detailed Progress Indicators
==============================================
Shows detailed progress during model training
"""

import sys
import os
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from core.enhanced_anomaly_detector import EnhancedAnomalyDetector
    IMPORTS_AVAILABLE = True
except ImportError as e:
    print(f"❌ Cannot import detector: {e}")
    print(f"   Please install dependencies: pip3 install -r requirements.txt")
    sys.exit(1)

def print_step(step_num: int, total_steps: int, message: str):
    """Print formatted step message"""
    percent = (step_num / total_steps) * 100
    print(f"\n[{step_num}/{total_steps}] {percent:.0f}% - {message}")
    sys.stdout.flush()

def train_with_detailed_progress(dataset_file: str):
    """Train models with detailed progress output"""
    print("="*70)
    print("🧠 TRAINING ML MODELS WITH REALISTIC DATA")
    print("="*70)
    
    # Initialize detector
    print("\n🔧 Initializing ML detector...")
    detector = EnhancedAnomalyDetector({
        'contamination': 0.05,
        'nu': 0.05,
        'pca_components': 10
    })
    print(f"   ✅ Detector initialized")
    print(f"   📁 Model directory: {detector.model_dir}")
    
    # Load training data
    print(f"\n📂 Loading training data from {dataset_file}...")
    start_time = time.time()
    training_data = detector.load_training_data_from_file(dataset_file)
    
    if not training_data:
        print("❌ No training data loaded")
        return False
    
    load_time = time.time() - start_time
    print(f"   ✅ Loaded {len(training_data)} samples")
    print(f"   ⏱️  Load time: {load_time:.2f} seconds")
    
    # Train models (this will show progress from our enhanced train_models method)
    print(f"\n🧠 Starting model training...")
    training_start = time.time()
    
    detector.train_models(training_data, append=False)
    
    total_time = time.time() - training_start
    print(f"\n" + "="*70)
    print(f"✅ TRAINING COMPLETE!")
    print(f"="*70)
    print(f"📊 Final Summary:")
    print(f"   - Training samples: {len(training_data)}")
    print(f"   - Total training time: {total_time:.2f} seconds ({total_time/60:.1f} minutes)")
    print(f"   - Models location: {detector.model_dir}")
    print(f"   - Models fitted: {detector.is_fitted}")
    print(f"   - Models trained: {detector.models_trained}")
    
    # Verify models
    print(f"\n🔍 Verifying trained models...")
    if detector.is_fitted:
        print(f"   ✅ Models are ready for detection")
        
        # Quick test
        print(f"\n🧪 Quick detection test...")
        test_syscalls = ['read', 'write', 'open', 'close'] * 10
        test_info = {'cpu_percent': 10.0, 'memory_percent': 5.0, 'num_threads': 2}
        result = detector.detect_anomaly_ensemble(test_syscalls, test_info, pid=9999)
        print(f"   Test result: Score={result.anomaly_score:.2f}, IsAnomaly={result.is_anomaly}")
        print(f"   ✅ Detection test passed!")
    else:
        print(f"   ❌ Models not properly fitted")
        return False
    
    return True

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Train models with detailed progress')
    parser.add_argument('--file', type=str, required=True,
                       help='Path to training data JSON file')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.file):
        print(f"❌ File not found: {args.file}")
        return 1
    
    success = train_with_detailed_progress(args.file)
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())

