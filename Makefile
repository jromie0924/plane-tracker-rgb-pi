.PHONY: test test-unit test-integration test-all help run release-info

# Default target
help:
	@echo "Available targets:"
	@echo ""
	@echo "Application:"
	@echo "  make start            - Start the plane tracker application"
	@echo ""
	@echo "Testing:"
	@echo "  make test             - Run all tests (24 tests)"
	@echo "  make test-unit        - Run unit tests (5 tests for matrix_service)"
	@echo "  make test-integration - Run integration tests (10 tests for imports)"
	@echo "  make test-all         - Run all tests with verbose output"
	@echo "  make test-service     - Run service tests (9 tests for adsbTracker)"
	@echo ""
	@echo "Release:"
	@echo "  make release-info     - Show instructions for promoting RC to main"
	@echo ""
	@echo "Usage:"
	@echo "  1. Ensure you're in pipenv shell: pipenv shell"
	@echo "  2. Run desired target: make start or make test"

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

# Start tracking server
start:
	scripts/start-tracker.sh

# Release information
release-info:
	@echo "==========================================="
	@echo "   Promoting RC to Main (Release Process)"
	@echo "==========================================="
	@echo ""
	@echo "To promote RC branch to main and create a release:"
	@echo ""
	@echo "1. Go to the Actions tab in GitHub:"
	@echo "   https://github.com/jromie0924/plane-tracker-rgb-pi/actions"
	@echo ""
	@echo "2. Select 'Promote RC to Main' workflow"
	@echo ""
	@echo "3. Click 'Run workflow'"
	@echo ""
	@echo "4. Enter version number using semantic versioning:"
	@echo "   Examples: v1.0.0, v1.2.3, v2.0.0"
	@echo ""
	@echo "5. Click 'Run workflow' to start the promotion"
	@echo ""
	@echo "The action will:"
	@echo "  - Merge RC into main (no fast-forward)"
	@echo "  - Create a git tag with your version"
	@echo "  - Push the merge commit and tag to main"
	@echo ""
	@echo "For more details, see BRANCHING.md"
	@echo "==========================================="