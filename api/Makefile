check: ## Run checks
check: check-static test

check-static: ## Run static code checks
check-static: format-check lint

clean: ## Remove intermediate, cache, or build artifacts
	find . -type f -name '*.py[co]' -delete
	find . -type d -name __pycache__ -exec rm -rv {} +
	rm -rf massgov.egg-info
	rm -rf dist
	-poetry run coverage erase # takes care of .coverage file
	rm -rf .coverage_report
	rm -f .testmondata

clean-venv: ## Remove active poetry virtualenv
	rm -rf $(shell poetry env info --path)

deps: ## Install dependencies
	poetry install --no-root

build: ## Build container
	docker build --tag mass-pfml-api .

run: ## Run docker-compose
	docker-compose up --detach; docker logs --follow mass-pfml-api

stop: ## Stop running containers
	docker-compose down

format: ## Format code
	poetry run isort --atomic --apply
	poetry run black .

format-check: ## Check format of code
	poetry run isort --atomic --check-only
	poetry run black . --check

lint: ## Run linting
	poetry run flake8 .

test: ## Run tests
	poetry run coverage run --branch --source=massgov -m pytest
	poetry run coverage report

test-changed: ## Run only tests that have changed
	poetry run python -m pytest --testmon

test-watch: ## Watch and run tests on file changes
	poetry run pytest-watch --runner "make test-changed"

# Get open command for Linux/Mac
UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Linux)
	OPEN_CMD := xdg-open
endif
ifeq ($(UNAME_S),Darwin)
	OPEN_CMD := open
endif

test-coverage-report: ## Open HTML test coverage report
	poetry run coverage html --directory .coverage_report
	$(OPEN_CMD) .coverage_report/index.html
