"""Test runner script."""

import subprocess
import sys


def run_tests():
    """Run all tests with coverage."""
    cmd = [
        "venv_converter\\Scripts\\python.exe", "-m", "pytest",
        "tests/",
        "-v",
        "--tb=short",
        "--cov=converter",
        "--cov=web_converter",
        "--cov-report=term-missing",
        "--cov-report=html",
        "--cov-fail-under=80",
        "-x",  # Stop on first failure
    ]
    
    result = subprocess.run(cmd, cwd=r"D:\Downloads\Go fr\File converter")
    return result.returncode


def run_unit_tests():
    """Run only unit tests."""
    cmd = [
        "venv_converter\\Scripts\\python.exe", "-m", "pytest",
        "tests/test_core.py",
        "tests/test_handlers.py",
        "-v",
        "--tb=short",
    ]
    return subprocess.run(cmd, cwd=r"D:\Downloads\Go fr\File converter").returncode


def run_integration_tests():
    """Run only integration tests."""
    cmd = [
        "venv_converter\\Scripts\\python.exe", "-m", "pytest",
        "tests/test_api.py",
        "-v",
        "--tb=short",
    ]
    return subprocess.run(cmd, cwd=r"D:\Downloads\Go fr\File converter").returncode


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "unit":
            sys.exit(run_unit_tests())
        elif sys.argv[1] == "integration":
            sys.exit(run_integration_tests())
        elif sys.argv[1] == "all":
            sys.exit(run_tests())
    else:
        print("Usage: python run_tests.py [unit|integration|all]")
        sys.exit(1)