#!/bin/bash

echo "Setting up test environment..."

# Create virtual environment if it doesn't exist
if [ ! -d "test_venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv test_venv
fi

# Activate virtual environment
source test_venv/bin/activate

# Install dependencies
echo "Installing test dependencies..."
pip install -q pytest pytest-asyncio pytest-mock playwright

echo -e "\n========================================"
echo "Running Sailor Site MCP Tests"
echo "========================================"

# Run unit tests
echo -e "\n--- Running Unit Tests ---"
python -m pytest tests/unit/ -v --tb=short -m "not integration"

# Check if unit tests passed
if [ $? -eq 0 ]; then
    echo -e "\n✅ Unit tests passed!"
    
    # Run integration tests (optional)
    echo -e "\n--- Running Integration Tests ---"
    echo "Note: Integration tests require Playwright browser"
    python -m pytest tests/integration/ -v --tb=short -m "integration" || echo "⚠️  Integration tests require browser setup"
else
    echo -e "\n❌ Unit tests failed!"
    exit 1
fi

# Generate coverage report if coverage is installed
if command -v coverage &> /dev/null; then
    echo -e "\n--- Generating Coverage Report ---"
    coverage run -m pytest tests/unit/
    coverage report
fi

echo -e "\n========================================"
echo "Test run complete!"
echo "========================================"

deactivate