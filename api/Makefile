# Docker user configuration
#
# Can be set by adding user=<username> and/ or uid=<id> to make command.
#
# If variables are not set explicitly: try looking up values from current
# environment, otherwise fixed defaults.
#
# uid= defaults to 0 if user= set (which makes sense if user=root, otherwise you
# probably want to set uid as well).
#
# Tested to work consistently on popular Linux flavors and Mac.
ifeq ($(user),)
RUN_USER ?= $(or $(strip $(USER)),nodummy)
RUN_UID ?= $(or $(strip $(shell id -u)),4000)
else
RUN_USER = $(user)
RUN_UID = $(or $(strip $(uid)),0)
endif

export RUN_USER
export RUN_UID

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

clean-docker: ## Remove project docker artifacts
	docker-compose down --remove-orphans --rmi all --volumes

clean-venv: ## Remove active poetry virtualenv
	rm -rf $(shell poetry env info --path)

build: ## Build container
	docker-compose build

deps: ## Install dependencies
	poetry install --no-root

format: ## Format code
	poetry run isort --atomic --apply
	poetry run black .

format-check: ## Check format of code
	poetry run isort --atomic --check-only
	poetry run black . --check

lint: ## Run linting
	poetry run flake8 .

login: start ## Start shell in running container
	docker exec -it mass-pfml-api sh

logs: start ## View API logs
	docker-compose logs --follow mass-pfml-api

logs-db: start ## View DB logs
	docker-compose logs --follow mass-pfml-db

start: ## Start containers
	docker-compose up --detach

stop: ## Stop running containers
	docker-compose down

run: ## Run docker-compose
run: start logs

test: ## Run tests
	poetry run coverage run --branch --source=massgov -m pytest
	poetry run coverage report

test-changed: ## Run only tests that have changed
	poetry run python -m pytest --testmon

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

test-watch: ## Watch and run tests on file changes
	poetry run pytest-watch --runner "make test-changed"
