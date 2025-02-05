# Contributing to Knowledge Synthesizer

Thank you for your interest in contributing to Knowledge Synthesizer! We welcome contributions from the community and are grateful for any help you can provide.

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the issue list as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible:

- Use a clear and descriptive title
- Describe the exact steps to reproduce the problem
- Provide specific examples to demonstrate the steps
- Describe the behavior you observed and what behavior you expected to see
- Include any error messages or logs

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

- A clear and descriptive title
- A detailed description of the proposed functionality
- Any possible drawbacks or alternatives you've considered
- If possible, a rough implementation approach

### Pull Requests

- Fill in the required template
- Follow the Python coding style (PEP 8)
- Include appropriate tests
- Update documentation as needed
- End all files with a newline

## Development Process

1. Fork the repo
2. Create a new branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run the tests (`./run_tests.sh`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Setting Up Development Environment

```bash
# Clone your fork
git clone https://github.com/edu-ap/knowledge-synthesizer.git
cd knowledge-synthesizer

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies and the package in development mode
pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install -e .

# Run tests
./run_tests.sh
```

## Project Structure

```
knowledge-synthesizer/
├── src/
│   └── knowledge_synthesizer/
│       ├── __init__.py
│       ├── cli.py          # Command-line interface
│       └── synthesizer.py  # Core functionality
├── tests/
│   ├── __init__.py
│   ├── test_cli.py
│   └── test_synthesizer.py
├── .env.example           # Template for environment variables
├── .gitignore
├── LICENSE
├── README.md
├── pyproject.toml        # Project metadata and dependencies
├── requirements.txt      # Production dependencies
├── requirements-dev.txt  # Development dependencies
└── run_tests.sh         # Test runner script
```

## Running Tests

```bash
# Run all tests
./run_tests.sh

# Run tests with coverage
pytest --cov=src/knowledge_synthesizer

# Run specific test file
pytest tests/test_cli.py

# Run tests in watch mode (requires pytest-watch)
ptw
```

## Code Style

- Follow PEP 8 guidelines
- Use meaningful variable names
- Add docstrings to functions and classes
- Comment complex logic
- Keep functions focused and small

### Code Formatting

We use several tools to maintain code quality:

```bash
# Format code with Black
black src tests

# Sort imports with isort
isort src tests

# Check code style with flake8
flake8 src tests

# Run type checking with mypy
mypy src
```

## Documentation

- Keep the README.md up to date with any user-facing changes
- Update docstrings for any modified functions
- Add type hints to new functions
- Document any new configuration options

## License

By contributing, you agree that your contributions will be licensed under the MIT License. 