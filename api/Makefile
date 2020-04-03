# Use -T to avoid making a pseudo-TTY, since docker-compose makes a real TTY by
# default. -T is needed for Github Actions to work properly with its version of
# docker-compose.
ifdef CI
	DOCKER_EXEC_ARGS := -T
endif

# For running Python things in the local environment (which could be when running inside a Docker container)
PY_RUN_CMD_POETRY := poetry run
# For running Python things in Docker, as one-off processes, starting container if needed
PY_RUN_CMD_DOCKER_RUN := docker-compose run $(DOCKER_EXEC_ARGS) --rm mass-pfml-api poetry run
# For running Python things in a running Docker container
PY_RUN_CMD_DOCKER_EXEC := docker-compose exec $(DOCKER_EXEC_ARGS) mass-pfml-api poetry run

ifdef CI
	PY_RUN_CMD_OPT ?= DOCKER_EXEC
else
	PY_RUN_CMD_OPT ?= POETRY
endif

PY_RUN_CMD := $(PY_RUN_CMD_$(PY_RUN_CMD_OPT))

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
	-$(PY_RUN_CMD) coverage erase # takes care of .coverage file
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
	$(PY_RUN_CMD) isort --atomic --apply
	$(PY_RUN_CMD) black .

format-check: ## Check format of code
	$(PY_RUN_CMD) isort --atomic --check-only
	$(PY_RUN_CMD) black . --check

lint: ## Run linting
	$(PY_RUN_CMD) flake8 .

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
	$(PY_RUN_CMD) coverage run --branch --source=massgov -m pytest
	$(PY_RUN_CMD) coverage report

test-changed: ## Run only tests that have changed
	$(PY_RUN_CMD) python -m pytest --testmon

# Get open command for Linux/Mac
UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Linux)
	OPEN_CMD := xdg-open
endif
ifeq ($(UNAME_S),Darwin)
	OPEN_CMD := open
endif

test-coverage-report: ## Open HTML test coverage report
	$(PY_RUN_CMD) coverage html --directory .coverage_report
	$(OPEN_CMD) .coverage_report/index.html

test-watch: ## Watch and run tests on file changes
	$(PY_RUN_CMD) pytest-watch --runner "make test-changed"
