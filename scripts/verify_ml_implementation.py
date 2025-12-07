#!/usr/bin/env python3
"""
Verify ML Implementation - Comprehensive Check
===============================================
This script verifies that the ML anomaly detection is properly implemented
and identifies any issues.
"""

import sys
import os
import pickle
import numpy as np
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from core.enhanced_anomaly_detector import EnhancedAnomalyDetector
    from sklearn.preprocessing import StandardScaler
    from sklearn.decomposition import PCA
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def check_model_files():
    """Check if model files exist"""
    print("=" * 70)
    print("1. CHECKING MODEL FILES")
    print("=" * 70)
    
    # Check default locations - prioritize current user's home directory
    import os
    current_user = os.getenv('USER', os.getenv('USERNAME', 'unknown'))
    is_root = (os.geteuid() == 0) if hasattr(os, 'geteuid') else False
    
    possible_dirs = []
    
    # Always check current user's home first
    user_home = Path.home()
    possible_dirs.append(user_home / '.cache' / 'security_agent' / 'models')
    
    # Only check root's directory if we're actually root
    if is_root:
        possible_dirs.append(Path('/root/.cache/security_agent/models'))
    elif current_user != 'root':
        # If not root, still check root's directory but handle permission errors
        possible_dirs.append(Path('/root/.cache/security_agent/models'))
    
    # Check project root
    possible_dirs.append(project_root / 'models')
    
    model_files = {
        'isolation_forest.pkl': False,
        'one_class_svm.pkl': False,
        'scaler.pkl': False,
        'pca.pkl': False
    }
    
    found_dir = None
    for model_dir in possible_dirs:
        try:
            if model_dir.exists():
                # Try to access the directory
                try:
                    list(model_dir.iterdir())  # Test read access
                    found_dir = model_dir
                    print(f"✅ Found model directory: {model_dir}")
                    for model_file in model_files.keys():
                        model_path = model_dir / model_file
                        if model_path.exists():
                            model_files[model_file] = True
                            size = model_path.stat().st_size
                            print(f"   ✅ {model_file}: {size:,} bytes")
                        else:
                            print(f"   ❌ {model_file}: NOT FOUND")
                    break
                except PermissionError:
                    print(f"⚠️  Found directory but no read permission: {model_dir}")
                    continue
        except Exception as e:
            # Skip directories that cause errors
            continue
    
    if not found_dir:
        print("❌ No model directory found in expected locations")
        print(f"   Checked: {[str(d) for d in possible_dirs]}")
        return None, model_files
    
    return found_dir, model_files

def check_model_loading():
    """Check if models can be loaded"""
    print("\n" + "=" * 70)
    print("2. CHECKING MODEL LOADING")
    print("=" * 70)
    
    detector = EnhancedAnomalyDetector()
    
    try:
        result = detector._load_models()
        print(f"✅ Model loading attempted")
        print(f"   is_fitted: {detector.is_fitted}")
        print(f"   models_trained: {detector.models_trained}")
        
        # Check individual components
        has_if = hasattr(detector, 'isolation_forest') and detector.isolation_forest is not None
        has_svm = hasattr(detector, 'one_class_svm') and detector.one_class_svm is not None
        has_scaler = hasattr(detector, 'scaler') and isinstance(detector.scaler, StandardScaler)
        has_pca = hasattr(detector, 'pca') and isinstance(detector.pca, PCA)
        
        print(f"\n   Component Status:")
        print(f"   - Isolation Forest: {'✅' if has_if else '❌'}")
        print(f"   - One-Class SVM: {'✅' if has_svm else '❌'}")
        print(f"   - Scaler: {'✅' if has_scaler else '❌'}")
        print(f"   - PCA: {'✅' if has_pca else '❌'}")
        
        if detector.is_fitted:
            # Check if models are actually trained
            if has_if:
                try:
                    # Try a dummy prediction
                    dummy_features = np.random.rand(1, 10)
                    pred = detector.isolation_forest.predict(dummy_features)
                    print(f"   ✅ Isolation Forest is functional (prediction works)")
                except Exception as e:
                    print(f"   ❌ Isolation Forest prediction failed: {e}")
            
            if has_svm:
                try:
                    dummy_features = np.random.rand(1, 10)
                    pred = detector.one_class_svm.predict(dummy_features)
                    print(f"   ✅ One-Class SVM is functional (prediction works)")
                except Exception as e:
                    print(f"   ❌ One-Class SVM prediction failed: {e}")
        
        return detector
    except Exception as e:
        print(f"❌ Error loading models: {e}")
        import traceback
        traceback.print_exc()
        return None

def check_feature_extraction(detector):
    """Check feature extraction"""
    print("\n" + "=" * 70)
    print("3. CHECKING FEATURE EXTRACTION")
    print("=" * 70)
    
    # Test with sample syscalls
    test_syscalls = ['read', 'write', 'open', 'close', 'mmap', 'munmap'] * 10
    test_process_info = {
        'cpu_percent': 10.0,
        'memory_percent': 5.0,
        'num_threads': 2
    }
    
    try:
        features = detector.extract_advanced_features(test_syscalls, test_process_info)
        print(f"✅ Feature extraction successful")
        print(f"   Feature vector shape: {features.shape}")
        print(f"   Feature vector length: {len(features)}")
        print(f"   Expected length: 50")
        
        if len(features) == 50:
            print(f"   ✅ Feature vector has correct length (50)")
        else:
            print(f"   ❌ Feature vector has wrong length (expected 50, got {len(features)})")
        
        # Check for NaN or Inf
        if np.any(np.isnan(features)):
            print(f"   ⚠️  Warning: Feature vector contains NaN values")
        if np.any(np.isinf(features)):
            print(f"   ⚠️  Warning: Feature vector contains Inf values")
        
        # Show feature statistics
        print(f"\n   Feature Statistics:")
        print(f"   - Min: {np.min(features):.4f}")
        print(f"   - Max: {np.max(features):.4f}")
        print(f"   - Mean: {np.mean(features):.4f}")
        print(f"   - Std: {np.std(features):.4f}")
        
        return True
    except Exception as e:
        print(f"❌ Feature extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_anomaly_detection(detector):
    """Check anomaly detection"""
    print("\n" + "=" * 70)
    print("4. CHECKING ANOMALY DETECTION")
    print("=" * 70)
    
    if not detector.is_fitted:
        print("❌ Models not fitted - cannot test anomaly detection")
        return False
    
    # Test with normal syscalls
    normal_syscalls = ['read', 'write', 'open', 'close', 'mmap', 'munmap'] * 10
    normal_info = {'cpu_percent': 10.0, 'memory_percent': 5.0, 'num_threads': 2}
    
    # Test with anomalous syscalls
    anomalous_syscalls = ['ptrace', 'mount', 'setuid', 'setgid', 'chroot'] * 10
    anomalous_info = {'cpu_percent': 90.0, 'memory_percent': 80.0, 'num_threads': 50}
    
    try:
        # Test normal
        print("\n   Testing NORMAL behavior:")
        normal_result = detector.detect_anomaly_ensemble(normal_syscalls, normal_info, pid=1234)
        print(f"   - Anomaly Score: {normal_result.anomaly_score:.2f}")
        print(f"   - Is Anomaly: {normal_result.is_anomaly}")
        print(f"   - Confidence: {normal_result.confidence:.2f}")
        print(f"   - Explanation: {normal_result.explanation[:100]}...")
        
        # Test anomalous
        print("\n   Testing ANOMALOUS behavior:")
        anomalous_result = detector.detect_anomaly_ensemble(anomalous_syscalls, anomalous_info, pid=5678)
        print(f"   - Anomaly Score: {anomalous_result.anomaly_score:.2f}")
        print(f"   - Is Anomaly: {anomalous_result.is_anomaly}")
        print(f"   - Confidence: {anomalous_result.confidence:.2f}")
        print(f"   - Explanation: {anomalous_result.explanation[:100]}...")
        
        # Check if scores make sense
        if normal_result.anomaly_score < anomalous_result.anomaly_score:
            print(f"\n   ✅ Scores are reasonable (normal < anomalous)")
        else:
            print(f"\n   ⚠️  Warning: Normal score ({normal_result.anomaly_score:.2f}) >= Anomalous score ({anomaly_result.anomaly_score:.2f})")
        
        return True
    except Exception as e:
        print(f"❌ Anomaly detection failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_model_configuration(detector):
    """Check model configuration"""
    print("\n" + "=" * 70)
    print("5. CHECKING MODEL CONFIGURATION")
    print("=" * 70)
    
    if hasattr(detector, 'isolation_forest') and detector.isolation_forest is not None:
        if_contamination = detector.isolation_forest.contamination
        print(f"   Isolation Forest contamination: {if_contamination}")
        if if_contamination == 0.05:
            print(f"   ✅ Contamination set to 0.05 (5%) - matches new configuration")
        elif if_contamination == 0.1:
            print(f"   ⚠️  Contamination is 0.1 (10%) - models trained with old config")
            print(f"      Recommendation: Retrain models with contamination=0.05")
        else:
            print(f"   ⚠️  Contamination is {if_contamination} - unexpected value")
    
    if hasattr(detector, 'one_class_svm') and detector.one_class_svm is not None:
        svm_nu = detector.one_class_svm.nu
        print(f"   One-Class SVM nu: {svm_nu}")
        if svm_nu == 0.05:
            print(f"   ✅ Nu set to 0.05 (5%) - matches new configuration")
        elif svm_nu == 0.1:
            print(f"   ⚠️  Nu is 0.1 (10%) - models trained with old config")
            print(f"      Recommendation: Retrain models with nu=0.05")
        else:
            print(f"   ⚠️  Nu is {svm_nu} - unexpected value")

def main():
    """Main verification function"""
    print("\n" + "=" * 70)
    print("ML IMPLEMENTATION VERIFICATION")
    print("=" * 70)
    
    # Check model files
    model_dir, model_files = check_model_files()
    
    # Check model loading
    detector = check_model_loading()
    
    if detector is None:
        print("\n❌ Cannot proceed - models not loaded")
        return
    
    # Check feature extraction
    if not check_feature_extraction(detector):
        print("\n❌ Feature extraction failed")
        return
    
    # Check anomaly detection
    if detector.is_fitted:
        check_anomaly_detection(detector)
        check_model_configuration(detector)
    else:
        print("\n⚠️  Models not fitted - skipping anomaly detection tests")
        print("   Train models with: python3 scripts/train_with_dataset.py")
    
    print("\n" + "=" * 70)
    print("VERIFICATION COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    main()

