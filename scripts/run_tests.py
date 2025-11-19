#!/usr/bin/env python3
"""Simple test runner for Sailor MCP tests"""
import sys
import subprocess
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Check if pytest is available
try:
    import pytest
except ImportError:
    print("pytest not found. Installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pytest", "pytest-asyncio", "pytest-mock"])
    import pytest

# Run tests
if __name__ == "__main__":
    # Run all unit tests
    exit_code = pytest.main([
        "tests/unit/",
        "-v",
        "--tb=short",
        "-x"  # Stop on first failure
    ])
    
    sys.exit(exit_code)