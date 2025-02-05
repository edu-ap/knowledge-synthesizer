#!/bin/bash
set -e  # Exit on error

echo "Creating virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

echo "Installing package in development mode with test dependencies..."
pip install --upgrade pip
pip install -e ".[test]"

echo "Running tests with coverage..."
pytest -v --cov=knowledge_synthesizer --cov-report=term-missing --cov-report=html

# Open coverage report if tests pass
if [ $? -eq 0 ]; then
    echo "Tests passed! Opening coverage report..."
    if [ "$(uname)" == "Darwin" ]; then
        open htmlcov/index.html
    elif [ "$(expr substr $(uname -s) 1 5)" == "Linux" ]; then
        xdg-open htmlcov/index.html
    fi
fi 