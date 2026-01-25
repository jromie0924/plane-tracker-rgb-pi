.PHONY: test test-unit test-integration test-all help

# Default target
help:
	@echo "Available test targets:"
	@echo "  make test             - Run all tests (24 tests)"
	@echo "  make test-unit        - Run unit tests (5 tests for matrix_service)"
	@echo "  make test-integration - Run integration tests (10 tests for imports)"
	@echo "  make test-all         - Run all tests with verbose output"
	@echo "  make test-service     - Run service tests (9 tests for adsbTracker)"
	@echo ""
	@echo "Usage:"
	@echo "  1. Ensure you're in pipenv shell: pipenv shell"
	@echo "  2. Run desired test target: make test"

# Run all tests
test:
	pipenv run python -m pytest

# Run unit tests (matrix_service module)
test-unit:
	pipenv run python -m pytest test/test_matrix_service.py -v

# Run integration tests (import verification)
test-integration:
	pipenv run python -m pytest test/test_imports.py -v

# Run all tests with verbose output
test-all:
	pipenv run python -m pytest -v

# Run service tests
test-service:
	pipenv run python -m pytest test/service/ -v

# Run tests with coverage
test-coverage:
	pipenv run python -m pytest --cov=src --cov-report=html
	@echo "Coverage report generated in htmlcov/index.html"
