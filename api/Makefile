APP_NAME := mass-pfml-api

export AWS_DEFAULT_REGION := us-east-1

DOCKER_REPO ?= pfml-api
DOCKER_REGISTRY ?= 498823821309.dkr.ecr.us-east-1.amazonaws.com

# Generate a unique tag based solely on the git hash.
# This will be the identifier used for deployment via terraform.
RELEASE_TAG := $(shell git rev-parse HEAD)

# Generate an informational tag so we can see where every image comes from.
DATE := $(shell date -u '+%Y%m%d.%H%M%S')
INFO_TAG := $(DATE).$(USER)

# Use -T to avoid making a pseudo-TTY, since docker-compose makes a real TTY by
# default. -T is needed for Github Actions to work properly with its version of
# docker-compose.
ifdef CI
	DOCKER_EXEC_ARGS := -T
endif

# For running Python things in the local environment (which could be when running inside a Docker container)
PY_RUN_CMD_POETRY := poetry run
# For running Python things in Docker, as one-off processes, starting container if needed
PY_RUN_CMD_DOCKER_RUN := docker-compose run $(DOCKER_EXEC_ARGS) --rm $(APP_NAME) poetry run
# For running Python things in a running Docker container
PY_RUN_CMD_DOCKER_EXEC := docker-compose exec $(DOCKER_EXEC_ARGS) $(APP_NAME) poetry run

ifdef CI
	PY_RUN_CMD_OPT ?= DOCKER_RUN
else
	PY_RUN_CMD_OPT ?= POETRY
endif

PY_RUN_CMD := $(PY_RUN_CMD_$(PY_RUN_CMD_OPT))

# BuildKit is a more efficient builder for Docker, so use it by default
ifndef NO_BUILDKIT
	export DOCKER_BUILDKIT=1
	export COMPOSE_DOCKER_CLI_BUILD=1
endif

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
	find . -type d -name __pycache__ -print -exec rm -r {} +
	find . -type d -name '*.egg-info' -print -exec rm -r {} +
	find . -type d -name .mypy_cache -print -exec rm -r {} +
	rm -rf dist
	-$(PY_RUN_CMD) coverage erase # takes care of .coverage file
	rm -rf .coverage_report
	rm -f .testmondata

clean-docker: ## Remove project docker artifacts
	docker-compose down --remove-orphans --rmi all --volumes

clean-venv: ## Remove active poetry virtualenv
	rm -rf $(shell poetry env info --path)

build: ## Build development container
	docker-compose build

build-app: ## Build app container
	docker build \
		--tag $(APP_NAME):latest \
		--tag $(APP_NAME):$(RELEASE_TAG) \
		--target app \
		--build-arg RUN_USER=$(RUN_USER) \
		--build-arg RUN_UID=$(RUN_UID) \
		.

deps: ## Install dependencies
	poetry install --no-root

ecr-login: ## Login to ECR for Docker
	@echo "Authenticating Docker with ECR"
	ecr_login_cmd="$$(aws ecr get-login --no-include-email)" && $$ecr_login_cmd

format: ## Format code
	$(PY_RUN_CMD) isort --atomic --apply
	$(PY_RUN_CMD) black .

format-check: ## Check format of code
	$(PY_RUN_CMD) isort --atomic --check-only
	$(PY_RUN_CMD) black . --check

# A flake8 output format that is compatible with GitHub Actions to annotate PRs. A full repository path must be output
# so the path is prefixed with `api/`.
# See https://help.github.com/en/actions/reference/workflow-commands-for-github-actions
ifdef CI
 FLAKE8_FORMAT := '::warning file=api/%(path)s,line=%(row)d,col=%(col)d::%(code)s %(text)s'
else
 FLAKE8_FORMAT := default
endif

lint: ## Run linting
	$(PY_RUN_CMD) flake8 --format=$(FLAKE8_FORMAT) massgov tests
	$(PY_RUN_CMD) mypy massgov

login: start ## Start shell in running container
	docker exec -it $(APP_NAME) sh

login-db: ## Start psql with project environment variables
	PGPASSWORD=$$DB_PASSWORD psql --host=$$DB_HOST --username=$$DB_USERNAME $$DB_NAME

logs: start ## View API logs
	docker-compose logs --follow $(APP_NAME)

logs-db: start ## View DB logs
	docker-compose logs --follow mass-pfml-db

psql: login-db

start: ## Start containers
	docker-compose up --detach

secure: ## Run security linting
	$(PY_RUN_CMD) bandit -r . --number 3 --skip B101 -ll

stop: ## Stop running containers
	docker-compose down

release: ## Build and publish release image
release: release-build release-publish

release-build: ## Build release image
	docker build \
		--tag $(APP_NAME):latest \
		--tag $(APP_NAME):$(RELEASE_TAG) \
		--target app \
		--build-arg RUN_USER=container \
		--build-arg RUN_UID=4000 \
		.

# Since we have a time-based tag INFO_TAG, tagging and pushing are usually best
# to be done together, but you could tag then later push by setting INFO_TAG
# directly
release-publish: ## Tag and push release
release-publish: ecr-login release-tag release-push

release-push: ## Push release image to the registry
	docker push $(DOCKER_REGISTRY)/$(DOCKER_REPO):$(RELEASE_TAG)
	docker push $(DOCKER_REGISTRY)/$(DOCKER_REPO):$(INFO_TAG)

release-tag: ## Tag release image for registry
	docker tag $(APP_NAME):$(RELEASE_TAG) $(DOCKER_REGISTRY)/$(DOCKER_REPO):$(RELEASE_TAG)
	docker tag $(APP_NAME):$(RELEASE_TAG) $(DOCKER_REGISTRY)/$(DOCKER_REPO):$(INFO_TAG)

run: ## Run docker-compose
run: start logs

db-upgrade: ## Apply pending migrations to db
	$(PY_RUN_CMD) db-migrate-up

db-downgrade: ## Rollback last migration in db
	$(PY_RUN_CMD) db-migrate-down

db-downgrade-all: ## Rollback all migrations
	$(PY_RUN_CMD) db-migrate-down-all

db-migrate-create: check-migrate-msg ## Create a new migration based on model changes
	$(PY_RUN_CMD) alembic -c ./massgov/pfml/db/migrations/alembic.ini revision --autogenerate -m "$(MIGRATE_MSG)"

check-migrate-msg:
ifndef MIGRATE_MSG
	$(error MIGRATE_MSG is undefined)
endif

test: ## Run tests, set `args` to pass flags to `pytest`
	$(PY_RUN_CMD) coverage run --branch --source=massgov -m pytest $(args)
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
