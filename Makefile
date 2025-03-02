# Sets the default target to run when 'make' is invoked without arguments.
.DEFAULT_GOAL := all

# Defines a variable for the pytest executable, using poetry run.
PYTEST := poetry run pytest

# 'all' target. Runs tests and linting (once you add linting).
all: test

# 'test' target. Runs pytest. The '-v' flag provides verbose output.
# The '-s' flag allows output from print statements (useful for debugging).
test:
	$(PYTEST) -v -s tests/

# 'test-database' target. Runs only the database tests.
test-database:
	$(PYTEST) -v -s tests/test_database.py

# 'test-ecfr-service' target. Runs only the ecfr service tests.
test-ecfr-service:
	$(PYTEST) -v -s tests/test_ecfr_service.py

# 'test-integration' target. Runs only the integration tests.
test-integration:
	$(PYTEST) -v -s tests/test_integration.py

# 'clean' target. Removes temporary files and build artifacts.
clean:
	rm -rf __pycache__/
	rm -rf .pytest_cache/
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name "tmp*" -exec rm -rf {} +
	poetry cache clear --all pypi  # Clear Poetry's cache

# --- FastAPI Commands ---

# Run FastAPI using Uvicorn.
run-api:
	poetry run uvicorn app.web.api:app --reload --port 8000

# --- Gradio Command ---

# Run the Gradio UI.
run-ui:
	poetry run python app/web/ui.py

# Phony targets tell Make that these targets are not actual files.
.PHONY: all test test-database test-ecfr-service test-integration clean run-api run-ui 