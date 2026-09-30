"""
CampusHub - Academic Resource & Peer Study Group Scheduling System
Main Application Entry Point.

Usage:
  python main.py           # Launch Interactive Terminal Application
  python main.py --web     # Launch Browser Web Dashboard (http://localhost:8000)
  python main.py --seed    # Pre-populate sample database records
  python main.py --test    # Execute all automated unit and integration tests
"""

import argparse
import sys
import unittest
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from campushub.database.db_manager import get_db
from campushub.cli.menu import CampusHubCLI
from campushub.web.app import start_server


def run_unit_tests():
    """Discover and execute test suite."""
    print("\n=======================================================")
    print(" EXECUTING CAMPUSHUB AUTOMATED TEST SUITE")
    print("=======================================================\n")
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=str(BASE_DIR / "tests"), pattern="test_*.py")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)


def main():
    parser = argparse.ArgumentParser(
        description="CampusHub: Academic Resource & Peer Study Group Scheduling System"
    )
    parser.add_argument(
        "--web", "-w",
        action="store_true",
        help="Launch native zero-dependency web dashboard on http://127.0.0.1:8000",
    )
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=8000,
        help="Port for web dashboard (default: 8000)",
    )
    parser.add_argument(
        "--seed", "-s",
        action="store_true",
        help="Populate database with sample student, tutor, and session records",
    )
    parser.add_argument(
        "--test", "-t",
        action="store_true",
        help="Execute automated unit tests and exit",
    )

    args = parser.parse_args()

    if args.test:
        run_unit_tests()

    if args.seed:
        db = get_db()
        cli = CampusHubCLI(db)
        cli._seed_sample_data()
        print("Database seeding completed.")
        if not args.web:
            return

    if args.web:
        start_server(port=args.port)
    else:
        # Default: Interactive Terminal CLI
        db = get_db()
        cli = CampusHubCLI(db)
        cli.run()


if __name__ == "__main__":
    main()
1