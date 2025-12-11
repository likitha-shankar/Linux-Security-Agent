#!/usr/bin/env python3
"""
Generate Formalized Performance Benchmark Report
Creates comprehensive performance metrics documentation
"""

import sys
import os
import time
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def run_benchmark_script():
    """Run the benchmark script and capture output"""
    print("📊 Running Performance Benchmarks...")
    
    benchmark_script = project_root / "tests" / "benchmark_performance.py"
    if not benchmark_script.exists():
        print(f"⚠️  Benchmark script not found: {benchmark_script}")
        return None
    
    try:
        result = subprocess.run(
            [sys.executable, str(benchmark_script)],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        return {
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        }
    except subprocess.TimeoutExpired:
        return {'error': 'Benchmark timed out after 5 minutes'}
    except Exception as e:
        return {'error': str(e)}

def parse_benchmark_output(output: str) -> Dict[str, Any]:
    """Parse benchmark output to extract metrics"""
    metrics = {}
    
    # Extract events per second
    if 'Events/sec:' in output:
        for line in output.split('\n'):
            if 'Events/sec:' in line:
                try:
                    value = float(line.split('Events/sec:')[1].strip().replace(',', ''))
                    metrics['events_per_second'] = value
                except:
                    pass
    
    # Extract CPU usage
    if 'CPU usage:' in output:
        for line in output.split('\n'):
            if 'CPU usage:' in line:
                try:
                    value = float(line.split('CPU usage:')[1].strip().replace('%', ''))
                    metrics['cpu_usage_percent'] = value
                except:
                    pass
    
    # Extract memory per process
    if 'Per process:' in output:
        for line in output.split('\n'):
            if 'Per process:' in line:
                try:
                    value = float(line.split('Per process:')[1].strip().replace('KB', ''))
                    metrics['memory_per_process_kb'] = value
                except:
                    pass
    
    # Extract calculations per second
    if 'Calculations/sec:' in output:
        for line in output.split('\n'):
            if 'Calculations/sec:' in line:
                try:
                    value = float(line.split('Calculations/sec:')[1].strip().replace(',', ''))
                    metrics['risk_calculations_per_second'] = value
                except:
                    pass
    
    # Extract ML inferences per second
    if 'Inferences/sec:' in output:
        for line in output.split('\n'):
            if 'Inferences/sec:' in output:
                try:
                    value = float(line.split('Inferences/sec:')[1].strip().replace(',', ''))
                    metrics['ml_inferences_per_second'] = value
                except:
                    pass
    
    return metrics

def generate_report(benchmark_result: Dict[str, Any], metrics: Dict[str, Any]) -> str:
    """Generate formatted performance report"""
    report = []
    report.append("# Performance Benchmark Report\n")
    report.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    report.append("## Executive Summary\n\n")
    
    if benchmark_result.get('error'):
        report.append(f"❌ **Error:** {benchmark_result['error']}\n\n")
    elif benchmark_result.get('returncode') != 0:
        report.append(f"⚠️  **Warning:** Benchmark exited with code {benchmark_result.get('returncode')}\n\n")
    else:
        report.append("✅ **Status:** Benchmarks completed successfully\n\n")
    
    report.append("## Performance Metrics\n\n")
    
    if metrics:
        report.append("| Metric | Value |\n")
        report.append("|--------|-------|\n")
        
        if 'events_per_second' in metrics:
            report.append(f"| Event Processing Rate | {metrics['events_per_second']:,.0f} events/sec |\n")
        
        if 'cpu_usage_percent' in metrics:
            report.append(f"| CPU Usage | {metrics['cpu_usage_percent']:.2f}% |\n")
        
        if 'memory_per_process_kb' in metrics:
            report.append(f"| Memory per Process | {metrics['memory_per_process_kb']:.2f} KB |\n")
        
        if 'risk_calculations_per_second' in metrics:
            report.append(f"| Risk Score Calculations | {metrics['risk_calculations_per_second']:,.0f} calc/sec |\n")
        
        if 'ml_inferences_per_second' in metrics:
            report.append(f"| ML Inference Rate | {metrics['ml_inferences_per_second']:,.0f} inferences/sec |\n")
    else:
        report.append("⚠️  No metrics extracted from benchmark output.\n\n")
    
    report.append("\n## Benchmark Output\n\n")
    report.append("```\n")
    if benchmark_result.get('stdout'):
        report.append(benchmark_result['stdout'])
    if benchmark_result.get('stderr'):
        report.append("\nSTDERR:\n")
        report.append(benchmark_result['stderr'])
    report.append("\n```\n")
    
    report.append("\n## Notes\n\n")
    report.append("- These are benchmark results, not production metrics.\n")
    report.append("- Real-world performance may vary based on system load.\n")
    report.append("- Results are measured on a controlled test environment.\n")
    
    return ''.join(report)

def main():
    """Main function"""
    print("=" * 70)
    print("🚀 Performance Benchmark Report Generator")
    print("=" * 70)
    
    # Run benchmarks
    benchmark_result = run_benchmark_script()
    
    if not benchmark_result:
        print("❌ Failed to run benchmarks")
        return 1
    
    # Parse output
    output = benchmark_result.get('stdout', '')
    metrics = parse_benchmark_output(output)
    
    # Generate report
    report = generate_report(benchmark_result, metrics)
    
    # Save report
    report_file = project_root / "PERFORMANCE_BENCHMARK_REPORT.md"
    with open(report_file, 'w') as f:
        f.write(report)
    
    print(f"\n✅ Performance report saved to: {report_file}")
    
    # Also save JSON for programmatic access
    json_file = project_root / "performance_metrics.json"
    with open(json_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'metrics': metrics,
            'benchmark_output': benchmark_result.get('stdout', ''),
            'benchmark_error': benchmark_result.get('stderr', '')
        }, f, indent=2)
    
    print(f"✅ Metrics JSON saved to: {json_file}")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
