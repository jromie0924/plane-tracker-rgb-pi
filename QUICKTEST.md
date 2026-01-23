# Quick Test Guide

This is a simplified guide for running tests in the plane-tracker-rgb-pi project.

## Prerequisites

The project uses `pipenv` for dependency management. Make sure you have pipenv installed and are in the pipenv shell:

```bash
pipenv install --dev
pipenv shell
```

This will install all dependencies including pytest.

## Running Tests

### Quick Start - Run All Tests

```bash
python -m pytest
```

Expected result: `24 passed`

### Run Tests with Details

```bash
python -m pytest -v
```

### Run Specific Test Files

```bash
# Matrix service tests only
python -m pytest test/test_matrix_service.py -v

# Import tests only
python -m pytest test/test_imports.py -v

# Service tests only
python -m pytest test/service/ -v
```

### Run Matrix Service Tests (15 tests)

```bash
python -m pytest test/test_matrix_service.py test/test_imports.py -v
```

## Test Environment Variables

Force emulator or hardware mode:

```bash
# Force emulator mode
MATRIX_MODE=emulator python -m pytest -v

# Force hardware mode
MATRIX_MODE=hardware python -m pytest -v
```

## Test Coverage

Generate code coverage report:

```bash
python -m pytest --cov=src --cov-report=html
```

Open `htmlcov/index.html` in your browser to view the coverage report.

## Troubleshooting

**Problem:** Tests fail with "No module named 'pytest'"

**Solution:** Make sure you're in the pipenv shell:
```bash
pipenv shell
```

**Problem:** Import errors when running tests

**Solution:** Run tests from the project root directory:
```bash
cd plane-tracker-rgb-pi
python -m pytest
```

---

For detailed testing documentation, see [TESTING.md](TESTING.md).
