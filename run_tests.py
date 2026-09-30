"""
CampusHub Automated Test Runner Script.
Executes all unit tests with full reporting.
"""

import sys
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print(" CAMPUSHUB ACADEMIC SYSTEM - AUTOMATED UNIT TEST SUITE")
    print("=" * 60 + "\n")
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=str(BASE_DIR / "tests"), pattern="test_*.py")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
