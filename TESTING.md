# Testing Guide

This document describes how to run tests for the plane-tracker-rgb-pi project.

## Quick Start

The project uses `pipenv` for dependency management and includes a `Makefile` for easy test execution.

```bash
# 1. Set up pipenv environment
pipenv install --dev
pipenv shell

# 2. Run tests using make
make test              # Run all tests (24 tests)
make test-unit         # Run unit tests (5 tests)
make test-integration  # Run integration tests (10 tests)
make test-all          # Run all tests with verbose output
```

See `make help` for all available test targets.

Expected output: `24 passed`

## Test Structure

The project uses `pytest` as its testing framework. Tests are organized in the `test/` directory:

```
test/
├── service/
│   └── test_adsbTracker.py      # Tests for ADSB tracking service (has pre-existing issues)
├── test_matrix_service.py        # Unit tests for matrix_service module
└── test_imports.py               # Integration tests for import verification
```

**Note:** All tests now pass. The project uses `pipenv` for dependency management.

## Prerequisites

### Recommended: Using pipenv (Project Standard)

The project uses pipenv for dependency management:

```bash
pipenv install --dev
pipenv shell
```

This installs all dependencies including pytest from the Pipfile.

### Alternative: Using requirements file

If not using pipenv, install test dependencies from requirements file:

```bash
pip install -r requirements-test.txt
```

### Alternative: Direct pip install

Install pytest directly:

```bash
pip install pytest
```

## Running Tests

**Important:** Make sure you're in the pipenv shell before running tests:

```bash
pipenv shell
```

### Using Make (Recommended)

The project includes a Makefile with convenient test targets:

```bash
make help              # Show all available targets
make test              # Run all tests (24 tests)
make test-unit         # Run unit tests (5 tests for matrix_service)
make test-integration  # Run integration tests (10 tests for imports)
make test-all          # Run all tests with verbose output
make test-service      # Run service tests (9 tests for adsbTracker)
make test-coverage     # Run tests with coverage report
```

### Using pytest directly

You can also run pytest directly from the command line:

All commands should be run from the project root directory.

### Run All Tests

To run all tests in the project:

```bash
python -m pytest
```

### Run Tests with Verbose Output

For detailed output showing each test:

```bash
python -m pytest -v
```

### Run Tests for a Specific Module

To run tests for the matrix_service module:

```bash
python -m pytest test/test_matrix_service.py -v
```

To run integration tests:

```bash
python -m pytest test/test_imports.py -v
```

To run both matrix_service and import tests:

```bash
python -m pytest test/test_matrix_service.py test/test_imports.py -v
```

To run service tests:

```bash
python -m pytest test/service/ -v
```

### Run a Specific Test

To run a single test function:

```bash
python -m pytest test/test_matrix_service.py::test_is_raspberry_pi_detection_true -v
```

### Run Tests with Coverage

To see code coverage (requires pytest-cov):

```bash
python -m pytest --cov=src --cov-report=html
# Or use make
make test-coverage
```

This generates an HTML coverage report in `htmlcov/index.html`.

## Test Categories

### Unit Tests (`test/test_matrix_service.py`)

Tests the `matrix_service` module in isolation:
- **test_is_raspberry_pi_detection_true**: Verifies Raspberry Pi detection works
- **test_is_raspberry_pi_detection_false**: Verifies detection fails on non-Pi systems
- **test_force_emulator_mode**: Tests `MATRIX_MODE=emulator` override
- **test_force_hardware_mode**: Tests `MATRIX_MODE=hardware` override
- **test_matrix_service_exports**: Verifies all expected symbols are exported

### Integration Tests (`test/test_imports.py`)

Tests that all modules correctly import from `matrix_service`:
- **test_matrix_service_import**: Verifies matrix_service can be imported
- **test_colours_module_import**: Tests setup.colours imports graphics correctly
- **test_fonts_module_import**: Tests setup.fonts imports graphics correctly
- **test_journey_scene_import**: Tests scenes.journey imports graphics correctly
- **test_clock_scene_import**: Tests scenes.clock imports graphics correctly
- **test_flightdetails_scene_import**: Tests scenes.flightdetails imports graphics correctly
- **test_date_scene_import**: Tests scenes.date imports graphics correctly
- **test_all_modules_use_same_graphics_instance**: Verifies consistent graphics instance
- **test_emulator_mode_with_environment_variable**: Tests emulator mode override
- **test_hardware_mode_with_environment_variable**: Tests hardware mode override

### Service Tests (`test/service/test_adsbTracker.py`)

Tests the ADSB tracking service functionality.

## Environment Variables for Testing

The matrix_service module respects the `MATRIX_MODE` environment variable:

```bash
# Force emulator mode during tests
MATRIX_MODE=emulator python -m pytest test/test_imports.py -v

# Force hardware mode during tests
MATRIX_MODE=hardware python -m pytest test/test_imports.py -v
```

## Continuous Integration

Tests should pass before merging any pull request. The test suite validates:

1. **Platform abstraction**: matrix_service correctly detects and imports appropriate libraries
2. **Import integrity**: All modules successfully import from matrix_service
3. **Environment overrides**: Manual mode forcing works correctly
4. **Service functionality**: ADSB tracking and other services work as expected

## Troubleshooting

### ImportError: No module named 'pytest'

Make sure you're in the pipenv shell:
```bash
pipenv shell
```

If pytest is still not found, install dev dependencies:
```bash
pipenv install --dev
```

### Tests fail with "No module named 'RGBMatrixEmulator'"

This is expected in test environments. The tests mock these modules, so this error should not occur when running the test suite. If it does, ensure you're running tests through pytest, not importing modules directly.

### Tests fail with import errors

Ensure you're running tests from the project root directory:
```bash
cd plane-tracker-rgb-pi
python -m pytest
```

## Adding New Tests

When adding new functionality:

1. **Create test file**: Place in appropriate directory under `test/`
2. **Follow naming convention**: Test files should start with `test_`
3. **Use fixtures**: Leverage pytest fixtures for setup/teardown
4. **Mock external dependencies**: Use `unittest.mock` for external modules
5. **Test edge cases**: Include tests for error conditions and boundary cases

Example test structure:

```python
import pytest
from unittest.mock import MagicMock, patch

def test_my_feature():
    """Test description"""
    # Arrange
    expected = "expected_value"
    
    # Act
    result = my_function()
    
    # Assert
    assert result == expected
```

## Summary

- **Quick guide**: Run `make help` to see all test targets
- **Run all tests**: `make test` or `python -m pytest`
- **Run unit tests**: `make test-unit`
- **Run integration tests**: `make test-integration`
- **Run with details**: `make test-all` or `python -m pytest -v`
- **Force mode**: `MATRIX_MODE=emulator python -m pytest`

For questions or issues with tests, please open an issue on GitHub.
