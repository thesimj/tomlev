#!/usr/bin/env python3
"""Comprehensive quality check script for TomlEv.

This script runs all quality checks, including linting, type checking,
security scanning, documentation coverage, and complexity analysis.
"""

import subprocess
import sys
from pathlib import Path


def run_command(command: list[str], description: str) -> bool:
    """Run a command and return success status."""
    print(f"\n[CHECK] {description}")
    print(f"Running: {' '.join(command)}")

    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        if result.stdout:
            print(result.stdout)
        print(f"[PASS] {description} - PASSED")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[FAIL] {description} - FAILED")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False
    except FileNotFoundError:
        print(f"[SKIP] {description} - Tool not found")
        return False


def main():
    """Run all quality checks."""
    print("[START] TomlEv Quality Check Suite")
    print("=" * 50)

    # Change to the project root directory
    project_root = Path(__file__).parent.parent
    print(f"Project root: {project_root}")

    # List of checks to run
    checks = [
        # Code formatting and linting
        (["uv", "run", "ruff", "check"], "Ruff linting"),
        (["uv", "run", "ruff", "format", "--check"], "Ruff formatting check"),
        # Type checking
        (["uv", "run", "mypy", "tomlev"], "MyPy type checking"),
        # Security scanning
        (["uv", "run", "bandit", "-r", "tomlev"], "Bandit security scan"),
        # Documentation coverage
        (["uv", "run", "docstr-coverage", "tomlev", "--badge=no"], "Docstring coverage"),
        # Code complexity
        (["uv", "run", "radon", "cc", "tomlev", "-a"], "Code complexity analysis"),
        (["uv", "run", "radon", "mi", "tomlev"], "Maintainability index"),
        # Tests with coverage
        (["uv", "run", "pytest", "--cov", "--cov-report=term-missing", "--cov-fail-under=90"], "Test coverage"),
        # Property-based tests
        (["uv", "run", "pytest", "tests/test_property_based.py", "-v"], "Property-based tests"),
    ]

    # Track results
    passed = 0
    failed = 0

    for command, description in checks:
        if run_command(command, description):
            passed += 1
        else:
            failed += 1

    # Summary
    print("\n" + "=" * 50)
    print("[SUMMARY] QUALITY CHECK SUMMARY")
    print("=" * 50)
    print(f"[PASS] Passed: {passed}")
    print(f"[FAIL] Failed: {failed}")
    print(f"[STATS] Success rate: {passed / (passed + failed) * 100:.1f}%")

    if failed == 0:
        print("\n[SUCCESS] All quality checks passed! TomlEv is ready for release.")
        return 0
    else:
        print(f"\n[WARNING] {failed} quality checks failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
