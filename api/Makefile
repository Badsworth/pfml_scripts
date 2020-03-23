clean: ## Remove intermediate, cache, or build artifacts
	find . -type f -name '*.py[co]' -delete
	find . -type d -name __pycache__ -exec rm -rv {} +
	rm -rf massgov.egg-info
	rm -rf dist
	-poetry run coverage erase # takes care of .coverage file
	rm -rf .coverage_report

clean-venv: ## Remove active poetry virtualenv
	rm -rf $(shell poetry env info --path)

deps: ## Install dependencies
	poetry install --no-root

DOCKER_TAG := massgov_pfml_api:latest

docker-build: ## Build container for `DOCKER_TAG`
	docker build --tag=$(DOCKER_TAG) .

docker-run: ## Run `DOCKER_TAG`
	docker run --tty --interactive --disable-content-trust --publish=1550:1550 --rm $(DOCKER_TAG)

format: ## Format code
	poetry run isort --atomic --apply
	poetry run black .

format-check: ## Check format of code
	poetry run isort --atomic --check-only
	poetry run black . --check

lint: ## Run linting
	poetry run flake8 .

run-dev: ## Start development API server
	poetry run python -m massgov.pfml.api

test: ## Run tests
	poetry run coverage run --branch --source=massgov -m pytest
	poetry run coverage report

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
