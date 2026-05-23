.PHONY: test test-service test-api start release-info

# Run all tests with verbose output
test:
	pipenv run python -m pytest -v

# Run service tests
test-service:
	pipenv run python -m pytest test/service/ -v

test-api:
	pipenv run python -m pytest test/api/ -v

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