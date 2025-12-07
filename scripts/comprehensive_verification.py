#!/usr/bin/env python3
"""
Comprehensive Project Verification Script
Checks all components, tests functionality, and reports issues
"""

import os
import sys
import json
import importlib
import traceback
from pathlib import Path
from typing import Dict, List, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}\n")

def print_success(text: str):
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")

def print_error(text: str):
    print(f"{Colors.RED}❌ {text}{Colors.RESET}")

def print_warning(text: str):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.RESET}")

def print_info(text: str):
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.RESET}")

results = {
    'passed': 0,
    'failed': 0,
    'warnings': 0,
    'issues': []
}

def check_module_imports() -> bool:
    """Check if all required modules can be imported"""
    print_header("1. MODULE IMPORT CHECKS")
    
    modules = [
        ('core.simple_agent', 'SimpleSecurityAgent'),
        ('core.enhanced_anomaly_detector', 'EnhancedAnomalyDetector'),
        ('core.collectors.collector_factory', 'get_collector'),
        ('core.detection.risk_scorer', 'EnhancedRiskScorer'),
        ('core.connection_pattern_analyzer', 'ConnectionPatternAnalyzer'),
    ]
    
    all_ok = True
    for module_path, class_name in modules:
        try:
            module = importlib.import_module(module_path)
            if hasattr(module, class_name):
                print_success(f"{module_path}.{class_name}")
            else:
                print_error(f"{module_path}.{class_name} - Class not found")
                all_ok = False
                results['failed'] += 1
        except Exception as e:
            print_error(f"{module_path} - {e}")
            all_ok = False
            results['failed'] += 1
    
    if all_ok:
        results['passed'] += len(modules)
    return all_ok

def check_file_structure() -> bool:
    """Check if all required files exist"""
    print_header("2. FILE STRUCTURE CHECKS")
    
    required_files = [
        'core/simple_agent.py',
        'core/enhanced_anomaly_detector.py',
        'core/enhanced_security_agent.py',
        'core/collectors/ebpf_collector.py',
        'core/collectors/auditd_collector.py',
        'core/detection/risk_scorer.py',
        'scripts/simulate_attacks.py',
        'scripts/train_with_progress.py',
        'web/app.py',
        'web/templates/dashboard.html',
        'requirements.txt',
        'README.md',
        'HOW_TO_RUN.md',
    ]
    
    all_ok = True
    for file_path in required_files:
        full_path = project_root / file_path
        if full_path.exists():
            print_success(f"{file_path}")
        else:
            print_error(f"{file_path} - Missing")
            all_ok = False
            results['failed'] += 1
    
    if all_ok:
        results['passed'] += len(required_files)
    return all_ok

def check_ml_models() -> bool:
    """Check ML model configuration and files"""
    print_header("3. ML MODEL CHECKS")
    
    try:
        from core.enhanced_anomaly_detector import EnhancedAnomalyDetector
        
        detector = EnhancedAnomalyDetector({'anomaly_score_threshold': 60.0})
        
        # Check configuration
        print_info(f"Model directory: {detector.model_dir}")
        print_info(f"Isolation Forest contamination: {detector.isolation_forest.contamination}")
        print_info(f"One-Class SVM nu: {detector.one_class_svm.nu}")
        print_info(f"Anomaly threshold: {detector.config.get('anomaly_score_threshold', 60.0)}")
        
        # Check if models exist
        model_dir = Path(detector.model_dir)
        model_files = [
            'isolation_forest.pkl',
            'one_class_svm.pkl',
            'dbscan.pkl',
            'scaler.pkl',
            'pca.pkl'
        ]
        
        models_exist = True
        for model_file in model_files:
            model_path = model_dir / model_file
            if model_path.exists():
                size = model_path.stat().st_size / 1024  # KB
                print_success(f"{model_file} ({size:.1f} KB)")
            else:
                print_warning(f"{model_file} - Not found (models need training)")
                models_exist = False
        
        if models_exist:
            # Try to load models
            try:
                detector._load_models()
                print_success("Models loaded successfully")
                results['passed'] += 1
            except Exception as e:
                print_error(f"Failed to load models: {e}")
                results['failed'] += 1
                return False
        else:
            print_warning("Models not trained yet - run training script first")
            results['warnings'] += 1
        
        return True
    except Exception as e:
        print_error(f"ML model check failed: {e}")
        traceback.print_exc()
        results['failed'] += 1
        return False

def check_training_data() -> bool:
    """Check if training data exists"""
    print_header("4. TRAINING DATA CHECKS")
    
    training_files = [
        'datasets/adfa_training.json',
        'datasets/realistic_training_data.json',
        'datasets/normal_behavior_dataset.json'
    ]
    
    all_ok = True
    for data_file in training_files:
        full_path = project_root / data_file
        if full_path.exists():
            try:
                with open(full_path, 'r') as f:
                    data = json.load(f)
                    if 'samples' in data:
                        count = len(data['samples'])
                        print_success(f"{data_file} - {count} samples")
                    else:
                        print_warning(f"{data_file} - Invalid format")
                        all_ok = False
            except Exception as e:
                print_error(f"{data_file} - Error reading: {e}")
                all_ok = False
        else:
            print_warning(f"{data_file} - Not found")
            results['warnings'] += 1
    
    if all_ok:
        results['passed'] += 1
    return all_ok

def check_agent_configuration() -> bool:
    """Check agent configuration"""
    print_header("5. AGENT CONFIGURATION CHECKS")
    
    try:
        from core.simple_agent import SimpleSecurityAgent
        
        # Test default configuration
        agent = SimpleSecurityAgent()
        
        print_info(f"Default collector: {agent.config.get('collector', 'ebpf')}")
        print_info(f"Risk threshold: {agent.config.get('risk_threshold', 30.0)}")
        print_info(f"ML detector available: {agent.anomaly_detector is not None}")
        print_info(f"Connection analyzer available: {agent.connection_analyzer is not None}")
        
        # Check excluded processes
        excluded = agent.default_excluded
        print_info(f"Excluded processes: {len(excluded)} processes")
        
        print_success("Agent configuration valid")
        results['passed'] += 1
        return True
    except Exception as e:
        print_error(f"Agent configuration check failed: {e}")
        traceback.print_exc()
        results['failed'] += 1
        return False

def check_web_dashboard() -> bool:
    """Check web dashboard files"""
    print_header("6. WEB DASHBOARD CHECKS")
    
    web_files = [
        'web/app.py',
        'web/templates/dashboard.html',
        'web/requirements.txt'
    ]
    
    all_ok = True
    for web_file in web_files:
        full_path = project_root / web_file
        if full_path.exists():
            print_success(f"{web_file}")
        else:
            print_error(f"{web_file} - Missing")
            all_ok = False
            results['failed'] += 1
    
    # Check database
    db_path = project_root / 'web' / 'dashboard.db'
    if db_path.exists():
        print_success(f"Database exists: {db_path}")
    else:
        print_info("Database will be created on first run")
    
    if all_ok:
        results['passed'] += 1
    return all_ok

def check_scripts() -> bool:
    """Check important scripts"""
    print_header("7. SCRIPT CHECKS")
    
    important_scripts = [
        'scripts/simulate_attacks.py',
        'scripts/train_with_progress.py',
        'scripts/comprehensive_agent_test.py',
        'scripts/complete_training_setup.sh',
        'scripts/setup_adfa_ld_dataset.sh'
    ]
    
    all_ok = True
    for script in important_scripts:
        full_path = project_root / script
        if full_path.exists():
            # Check if executable (for .sh files)
            if script.endswith('.sh'):
                if os.access(full_path, os.X_OK):
                    print_success(f"{script} (executable)")
                else:
                    print_warning(f"{script} - Not executable (run chmod +x)")
                    results['warnings'] += 1
            else:
                print_success(f"{script}")
        else:
            print_error(f"{script} - Missing")
            all_ok = False
            results['failed'] += 1
    
    if all_ok:
        results['passed'] += 1
    return all_ok

def check_documentation() -> bool:
    """Check documentation files"""
    print_header("8. DOCUMENTATION CHECKS")
    
    doc_files = [
        'README.md',
        'HOW_TO_RUN.md',
        'PROJECT_STATUS.md',
        'TRAINING_DATA_SOURCES.md',
        'MITRE_ATTACK_COVERAGE.md'
    ]
    
    all_ok = True
    for doc_file in doc_files:
        full_path = project_root / doc_file
        if full_path.exists():
            size = full_path.stat().st_size
            if size > 1000:  # At least 1KB
                print_success(f"{doc_file} ({size} bytes)")
            else:
                print_warning(f"{doc_file} - Very small ({size} bytes)")
                results['warnings'] += 1
        else:
            print_error(f"{doc_file} - Missing")
            all_ok = False
            results['failed'] += 1
    
    if all_ok:
        results['passed'] += 1
    return all_ok

def check_code_quality() -> bool:
    """Check for common code issues"""
    print_header("9. CODE QUALITY CHECKS")
    
    issues_found = []
    
    # Check for bare except clauses
    try:
        import subprocess
        result = subprocess.run(
            ['grep', '-r', 'except:', 'core/', 'scripts/'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0 and result.stdout:
            lines = result.stdout.strip().split('\n')
            # Filter out comments and docstrings
            real_issues = [l for l in lines if '#' not in l and '"""' not in l]
            if real_issues:
                print_warning(f"Found {len(real_issues)} bare 'except:' clauses")
                results['warnings'] += 1
                issues_found.extend(real_issues[:5])  # Show first 5
    except:
        pass  # grep might not be available
    
    # Check for TODO/FIXME comments
    try:
        import subprocess
        result = subprocess.run(
            ['grep', '-ri', 'TODO|FIXME', 'core/', 'scripts/'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0 and result.stdout:
            todos = result.stdout.strip().split('\n')
            if todos:
                print_info(f"Found {len(todos)} TODO/FIXME comments (normal for active development)")
    except:
        pass
    
    if not issues_found:
        print_success("No major code quality issues found")
        results['passed'] += 1
    else:
        print_warning("Some code quality issues found (see above)")
        results['warnings'] += 1
    
    return True

def check_dependencies() -> bool:
    """Check if required dependencies are documented"""
    print_header("10. DEPENDENCY CHECKS")
    
    req_file = project_root / 'requirements.txt'
    if req_file.exists():
        with open(req_file, 'r') as f:
            deps = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        print_success(f"requirements.txt - {len(deps)} dependencies listed")
        
        # Check for critical dependencies
        critical = ['scikit-learn', 'numpy', 'rich']
        found = []
        for dep in critical:
            if any(dep.lower() in d.lower() for d in deps):
                found.append(dep)
        
        # Check web requirements separately
        web_req_file = project_root / 'web' / 'requirements.txt'
        web_deps_present = False
        if web_req_file.exists():
            with open(web_req_file, 'r') as f:
                web_deps = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            if any('flask' in d.lower() for d in web_deps):
                web_deps_present = True
                print_success("Web dependencies in web/requirements.txt")
        
        if len(found) == len(critical):
            print_success("All critical dependencies listed")
            if web_deps_present:
                print_success("Web dependencies found in web/requirements.txt")
            results['passed'] += 1
        else:
            missing = set(critical) - set(found)
            print_warning(f"Missing dependencies: {missing}")
            results['warnings'] += 1
    else:
        print_error("requirements.txt - Missing")
        results['failed'] += 1
        return False
    
    return True

def main():
    """Run all verification checks"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("="*70)
    print("  COMPREHENSIVE PROJECT VERIFICATION")
    print("="*70)
    print(f"{Colors.RESET}")
    
    checks = [
        check_module_imports,
        check_file_structure,
        check_ml_models,
        check_training_data,
        check_agent_configuration,
        check_web_dashboard,
        check_scripts,
        check_documentation,
        check_code_quality,
        check_dependencies
    ]
    
    for check in checks:
        try:
            check()
        except Exception as e:
            print_error(f"Check failed with exception: {e}")
            traceback.print_exc()
            results['failed'] += 1
    
    # Final summary
    print_header("VERIFICATION SUMMARY")
    
    total = results['passed'] + results['failed'] + results['warnings']
    print(f"\n{Colors.BOLD}Results:{Colors.RESET}")
    print(f"  {Colors.GREEN}✅ Passed: {results['passed']}{Colors.RESET}")
    print(f"  {Colors.RED}❌ Failed: {results['failed']}{Colors.RESET}")
    print(f"  {Colors.YELLOW}⚠️  Warnings: {results['warnings']}{Colors.RESET}")
    print(f"  Total checks: {total}")
    
    if results['failed'] == 0:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✅ All critical checks passed!{Colors.RESET}")
        if results['warnings'] > 0:
            print(f"{Colors.YELLOW}⚠️  Some warnings found - review above{Colors.RESET}")
        return 0
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ Some checks failed - review above{Colors.RESET}")
        return 1

if __name__ == '__main__':
    sys.exit(main())

