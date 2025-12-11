#!/usr/bin/env python3
"""
Comprehensive Test Suite - Real Testing on VM
Runs all tests, coverage, benchmarks, and attack simulations
NO SIMULATED RESULTS - All real tests
"""

import sys
import os
import subprocess
import time
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def run_command(cmd, description, timeout=300):
    """Run a command and return result"""
    print(f"\n{'='*70}")
    print(f"🔧 {description}")
    print(f"{'='*70}")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        print(f"Return code: {result.returncode}")
        if result.stdout:
            print("STDOUT:")
            print(result.stdout[:2000])  # First 2000 chars
            if len(result.stdout) > 2000:
                print(f"... ({len(result.stdout) - 2000} more characters)")
        if result.stderr:
            print("STDERR:")
            print(result.stderr[:1000])
        
        return {
            'success': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        }
    except subprocess.TimeoutExpired:
        print(f"❌ Command timed out after {timeout} seconds")
        return {'success': False, 'error': 'timeout'}
    except Exception as e:
        print(f"❌ Error: {e}")
        return {'success': False, 'error': str(e)}

def test_1_coverage():
    """Test 1: Run test coverage"""
    print("\n" + "="*70)
    print("TEST 1: Test Coverage Metrics")
    print("="*70)
    
    # Install coverage if needed
    print("Checking for coverage package...")
    try:
        import coverage
        print("✅ Coverage installed")
    except ImportError:
        print("Installing coverage...")
        subprocess.run([sys.executable, "-m", "pip", "install", "coverage", "pytest", "pytest-cov"], check=True)
    
    # Run coverage
    result = run_command(
        [sys.executable, "scripts/run_tests_with_coverage.py"],
        "Running tests with coverage"
    )
    
    # Check if coverage report exists
    coverage_file = project_root / "COVERAGE_REPORT.md"
    if coverage_file.exists():
        print(f"✅ Coverage report generated: {coverage_file}")
        with open(coverage_file, 'r') as f:
            content = f.read()
            print("\nCoverage Summary:")
            if "Total Coverage:" in content:
                for line in content.split('\n'):
                    if "Total Coverage:" in line:
                        print(f"  {line.strip()}")
    else:
        print("⚠️  Coverage report not found")
    
    return result

def test_2_ml_metrics():
    """Test 2: ML Metrics Integration"""
    print("\n" + "="*70)
    print("TEST 2: ML Metrics Integration")
    print("="*70)
    
    # Check if ML evaluator exists
    ml_eval_script = project_root / "scripts" / "evaluate_ml_models.py"
    if not ml_eval_script.exists():
        print("⚠️  ML evaluation script not found")
        return {'success': False, 'error': 'script not found'}
    
    # Run ML evaluation
    result = run_command(
        [sys.executable, str(ml_eval_script)],
        "Running ML model evaluation",
        timeout=600  # 10 minutes for ML evaluation
    )
    
    return result

def test_3_performance_benchmarks():
    """Test 3: Performance Benchmarks"""
    print("\n" + "="*70)
    print("TEST 3: Performance Benchmarks")
    print("="*70)
    
    # Run performance benchmark report generator
    result = run_command(
        [sys.executable, "scripts/generate_performance_report.py"],
        "Generating performance benchmark report"
    )
    
    # Check if report exists
    report_file = project_root / "PERFORMANCE_BENCHMARK_REPORT.md"
    if report_file.exists():
        print(f"✅ Performance report generated: {report_file}")
    else:
        print("⚠️  Performance report not found")
    
    return result

def test_4_attack_simulation():
    """Test 4: Attack Simulation"""
    print("\n" + "="*70)
    print("TEST 4: Attack Simulation Tests")
    print("="*70)
    
    # Run attack simulation
    result = run_command(
        [sys.executable, "scripts/simulate_attacks.py"],
        "Running attack simulations"
    )
    
    return result

def test_5_agent_integration():
    """Test 5: Agent Integration Test"""
    print("\n" + "="*70)
    print("TEST 5: Agent Integration Test")
    print("="*70)
    
    # Run integration tests
    result = run_command(
        [sys.executable, "-m", "pytest", "tests/test_integration.py", "-v"],
        "Running integration tests"
    )
    
    return result

def test_6_automated_tests():
    """Test 6: Automated Test Suite"""
    print("\n" + "="*70)
    print("TEST 6: Automated Test Suite")
    print("="*70)
    
    # Run automated tests
    result = run_command(
        [sys.executable, "scripts/automate_all_tests.py"],
        "Running automated test suite",
        timeout=600
    )
    
    return result

def generate_final_report(results):
    """Generate final comprehensive test report"""
    report_file = project_root / "COMPREHENSIVE_TEST_REPORT.md"
    
    with open(report_file, 'w') as f:
        f.write("# Comprehensive Test Report\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("## Test Results Summary\n\n")
        
        total_tests = len(results)
        passed_tests = sum(1 for r in results.values() if r.get('success'))
        
        f.write(f"- **Total Tests:** {total_tests}\n")
        f.write(f"- **Passed:** {passed_tests}\n")
        f.write(f"- **Failed:** {total_tests - passed_tests}\n")
        f.write(f"- **Pass Rate:** {(passed_tests/total_tests*100) if total_tests > 0 else 0:.1f}%\n\n")
        
        f.write("## Detailed Results\n\n")
        
        for test_name, result in results.items():
            status = "✅ PASS" if result.get('success') else "❌ FAIL"
            f.write(f"### {test_name}: {status}\n\n")
            
            if result.get('error'):
                f.write(f"**Error:** {result['error']}\n\n")
            elif result.get('returncode') is not None:
                f.write(f"**Return Code:** {result['returncode']}\n\n")
            
            if result.get('stdout'):
                f.write("**Output:**\n```\n")
                f.write(result['stdout'][:1000])  # First 1000 chars
                f.write("\n```\n\n")
        
        f.write("\n## Notes\n\n")
        f.write("- All tests run on real VM with actual eBPF and auditd\n")
        f.write("- No simulated results - all metrics are real\n")
        f.write("- Tests may take several minutes to complete\n")
    
    print(f"\n✅ Comprehensive test report saved to: {report_file}")
    return report_file

def main():
    """Main test runner"""
    print("="*70)
    print("🚀 COMPREHENSIVE TEST SUITE")
    print("="*70)
    print(f"Project Root: {project_root}")
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n⚠️  WARNING: This will run REAL tests on the VM")
    print("   - No simulated results")
    print("   - All tests use actual eBPF/auditd")
    print("   - May take 10-20 minutes to complete")
    print("="*70)
    
    results = {}
    
    # Run all tests
    results['Test Coverage'] = test_1_coverage()
    results['ML Metrics'] = test_2_ml_metrics()
    results['Performance Benchmarks'] = test_3_performance_benchmarks()
    results['Attack Simulation'] = test_4_attack_simulation()
    results['Agent Integration'] = test_5_agent_integration()
    results['Automated Tests'] = test_6_automated_tests()
    
    # Generate final report
    report_file = generate_final_report(results)
    
    # Print summary
    print("\n" + "="*70)
    print("📊 FINAL SUMMARY")
    print("="*70)
    
    total = len(results)
    passed = sum(1 for r in results.values() if r.get('success'))
    
    print(f"Total Tests: {total}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {total - passed} ❌")
    print(f"Pass Rate: {(passed/total*100) if total > 0 else 0:.1f}%")
    
    print(f"\n✅ Full report: {report_file}")
    
    return 0 if passed == total else 1

if __name__ == '__main__':
    sys.exit(main())
