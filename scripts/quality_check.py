#!/usr/bin/env python3
"""Comprehensive quality check script for TomlEv.

This script runs all quality checks, including linting, type checking,
security scanning, documentation coverage, and complexity analysis.
"""

import subprocess
import sys
from pathlib import Path


def run_candidates(candidates: list[list[str]], description: str) -> bool:
    """Try a list of candidate commands until one succeeds."""
    print(f"\n[CHECK] {description}")
    for command in candidates:
        print(f"Trying: {' '.join(command)}")
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            if result.stdout:
                print(result.stdout)
            print(f"[PASS] {description} - PASSED via: {' '.join(command)}")
            return True
        except FileNotFoundError:
            # Fall back to next candidate
            continue
        except subprocess.CalledProcessError as e:
            # Some environments (e.g., sandbox) may block uv; try next candidate
            if e.stdout:
                print("STDOUT:", e.stdout)
            if e.stderr:
                print("STDERR:", e.stderr)
            continue

    print(f"[FAIL] {description} - All candidates failed or unavailable")
    return False


def candidates_for(tool: str, *args: str) -> list[list[str]]:
    """Return a list of candidate invocations for a tool with given args."""
    bin_path = Path(".venv") / ("Scripts" if sys.platform.startswith("win") else "bin")
    exe = bin_path / tool
    candidates: list[list[str]] = [
        ["uv", "run", tool, *args],
        [str(exe), *args],
    ]
    # python -m fallbacks for common tools
    module_map = {
        "ruff": "ruff",
        "mypy": "mypy",
        "bandit": "bandit",
        "radon": "radon",
        "pytest": "pytest",
        # docstr-coverage package exposes module "docstr_coverage"
        "docstr-coverage": "docstr_coverage",
    }
    mod = module_map.get(tool)
    if mod:
        candidates.append([sys.executable, "-m", mod, *args])
    return candidates


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
        (candidates_for("ruff", "check"), "Ruff linting"),
        (candidates_for("ruff", "format", "--check"), "Ruff formatting check"),
        # Type checking
        (candidates_for("mypy", "tomlev"), "MyPy type checking"),
        # Security scanning
        (candidates_for("bandit", "-r", "tomlev"), "Bandit security scan"),
        # Documentation coverage
        (candidates_for("docstr-coverage", "tomlev", "--badge=no"), "Docstring coverage"),
        # Code complexity
        (candidates_for("radon", "cc", "tomlev", "-a"), "Code complexity analysis"),
        (candidates_for("radon", "mi", "tomlev"), "Maintainability index"),
        # Tests with coverage
        (candidates_for("pytest", "--cov", "--cov-report=term-missing", "--cov-fail-under=90"), "Test coverage"),
        # Property-based tests
        (candidates_for("pytest", "tests/test_property_based.py", "-v"), "Property-based tests"),
    ]

    # Track results
    passed = 0
    failed = 0

    for candidate_list, description in checks:
        if run_candidates(candidate_list, description):
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
