#!/usr/bin/env python3
"""
Master Verification Script for the Enterprise Policy RAG System.
Runs both the 10 Master Regression Tests (Phase 14) and 11 Acceptance Tests (Phase 21).
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.run_10_regression_tests import run_tests as run_regression_tests
from scripts.run_11_acceptance_tests import run_acceptance_tests

if __name__ == "__main__":
    print(">>> RUNNING MASTER REGRESSION TESTS (PHASE 14) <<<")
    reg_ok = run_regression_tests()
    
    print("\n>>> RUNNING ACCEPTANCE TESTS (PHASE 21) <<<")
    acc_ok = run_acceptance_tests()
    
    overall = reg_ok and acc_ok
    print("\n" + "=" * 80)
    print(f"MASTER SUITE STATUS: {'ALL SUITES PASSED (100%)' if overall else 'FAILURES DETECTED'}")
    print("=" * 80)
    sys.exit(0 if overall else 1)

