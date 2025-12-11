# Report Assets & Documentation

This document lists all assets available for the project report and demo.

## Screenshots

Located in `docs/screenshots/`:
- `Screenshot 2025-12-09 at 22.08.43.png` - Dashboard view
- `Screenshot 2025-12-09 at 22.09.22.png` - Dashboard metrics
- `Screenshot 2025-12-09 at 22.15.03.png` - Detection results
- `Screenshot 2025-12-09 at 23.54.52.png` - Dashboard activity
- `attack_test_report.png` - Attack test results
- `output.png` - Sample output
- `sample_output.png` - Sample output variant

## Reports & Logs

Located in `docs/reports/`:
- `COMPREHENSIVE_DEMO_LOG_10MIN.txt` - **Main verification log** (10-minute test, 373 lines)
  - Contains: Full test results, detection counts, system status
  - Key metrics: 72 port scans, 52 high-risk processes, 994 total events
- `COMPREHENSIVE_DEMO_LOG.txt` - Initial 3-minute test log
- `PROJECT_REPORT.html` - HTML project report

## Key Documentation

Located in `docs/`:
- `PROFESSOR_ATTACK_TESTING_QUESTIONS.md` - **Anticipated professor questions**
- `HOW_TO_RUN.md` - Setup and running instructions
- `ARCHITECTURE.md` - System architecture
- `MITRE_ATTACK_COVERAGE.md` - MITRE ATT&CK coverage
- `AUTOMATED_ATTACK_TESTS.md` - Attack testing documentation
- `GAP_ANALYSIS.md` - Gap analysis
- `PROFESSOR_TECHNICAL_ANSWERS.md` - Technical Q&A

## Test Results Summary

From `COMPREHENSIVE_DEMO_LOG_10MIN.txt`:

### Detection Results (10-minute test):
- **Port Scans Detected:** 72 ✅
- **High-Risk Processes:** 52 ✅
- **Total Syscalls Captured:** 994 ✅
- **C2 Beacons:** 0 ⚠️ (needs improvement)
- **ML Anomalies:** 0 ⚠️ (needs more training)

### System Performance:
- **CPU Usage:** ~3% (low overhead)
- **Memory Usage:** ~192MB
- **Agent Status:** ✅ Running
- **Dashboard Status:** ✅ Running (HTTP 200)

### Test Duration:
- **Start:** Thu Dec 11 18:32:52 UTC 2025
- **End:** Thu Dec 11 18:43:55 UTC 2025
- **Duration:** ~10 minutes

## Demo Scripts

Located in `scripts/`:
- `comprehensive_demo_verification.sh` - Full verification script
- `simulate_attacks.py` - Attack simulation
- `automate_all_tests.py` - Automated testing

## Quick Reference

### For Report:
1. Use `COMPREHENSIVE_DEMO_LOG_10MIN.txt` for test results
2. Reference screenshots from `docs/screenshots/`
3. Use `PROFESSOR_ATTACK_TESTING_QUESTIONS.md` for Q&A prep

### For Demo:
1. Run `scripts/comprehensive_demo_verification.sh` on VM
2. Show dashboard at `http://VM_IP:5001`
3. Reference detection counts from log file

---

*Last Updated: December 11, 2025*
