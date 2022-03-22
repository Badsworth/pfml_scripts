.DEFAULT_GOAL := help

APP_NAME := mass-pfml-api
SHELL = /bin/bash -o pipefail

export AWS_DEFAULT_REGION := us-east-1

DOCKER_REPO ?= pfml-api
# additional repo for 1099 image
DOCKER_PDF_REPO ?= pfml-pdf-api
DOCKER_REGISTRY ?= 498823821309.dkr.ecr.us-east-1.amazonaws.com

# Generate an informational tag so we can see where every image comes from.
DATE := $(shell date -u '+%Y%m%d.%H%M%S')
INFO_TAG := $(DATE).$(USER)

GIT_REPO_AVAILABLE := $(shell git rev-parse --is-inside-work-tree 2>/dev/null)

# Generate a unique tag based solely on the git hash.
# This will be the identifier used for deployment via terraform.
ifdef GIT_REPO_AVAILABLE
IMAGE_TAG := $(shell git rev-parse HEAD)
else
IMAGE_TAG := "uknown-dev.$(DATE)"
endif

# Use -T to avoid making a pseudo-TTY, since docker-compose makes a real TTY by
# default. -T is needed for Github Actions to work properly with its version of
# docker-compose.
ifdef CI
	DOCKER_EXEC_ARGS := -T -e CI -e PYTEST_ADDOPTS="--color=yes"
endif

# Path to Open API file for spectral linting
OPEN_API_PATH := openapi.yaml

# For running things in the local environment (which could be when running inside a Docker container)
RUN_CMD_NATIVE :=
# For running things in Docker, as one-off processes, starting container if needed
RUN_CMD_DOCKER_RUN := docker-compose run $(DOCKER_EXEC_ARGS) --rm $(APP_NAME)
# For running things in a running Docker container
RUN_CMD_DOCKER_EXEC := docker-compose exec $(DOCKER_EXEC_ARGS) $(APP_NAME)

RUN_CMD_OPT ?= DOCKER_RUN
RUN_CMD := $(RUN_CMD_$(RUN_CMD_OPT))

PY_RUN_CMD := $(RUN_CMD) poetry run

POETRY_CMD := $(RUN_CMD) poetry

ifeq "$(RUN_CMD)" ""
DECODE_LOG = 2>&1 | python3 -u massgov/pfml/util/logging/decodelog.py
else
# Docker already redirects stderr to stdout and doing it again can cause odd output.
DECODE_LOG := | python3 -u massgov/pfml/util/logging/decodelog.py
endif

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
	find . -type f -name '*.py[cod]' -delete
	find . -type d -name __pycache__ -print -exec rm -r {} +
	find . -type d -name '*.egg-info' -print -exec rm -r {} +
	find . -type d -name .mypy_cache -print -exec rm -r {} +
	find . -type d -name .pytest_cache -print -exec rm -r {} +
	rm -rf dist
	rm -f .coverage coverage.* .testmondata
	rm -rf .coverage_report
	find lambdas/ -type f -iname Makefile -exec sh -c '$(MAKE) -C $$(dirname {}) clean' \;

clean-docker: ## Remove project docker artifacts (which includes the DB)
	docker-compose down --remove-orphans --rmi all --volumes

clean-docker-volumes: ## Remove project docker volumes (which includes the DB state)
	docker-compose down --volumes

clean-venv: ## Remove active poetry virtualenv
	rm -rf $(shell poetry env info --path)

build: ## Build development container
	docker-compose build

build-app: ## Build app container
	docker build \
		--tag $(APP_NAME):latest \
		--tag $(APP_NAME):$(IMAGE_TAG) \
		--target app \
		--build-arg RUN_USER=$(RUN_USER) \
		--build-arg RUN_UID=$(RUN_UID) \
		.

create-erds:
	PYTHONPATH=$$PYTHONPATH:. $(PY_RUN_CMD) python bin/create-erds.py; rm *.dot; mv *.png ../docs/assets/api/erds

create-leave-admin-and-claims: ## Create local API Leave Admin user and claims
	PYTHONPATH=$$PYTHONPATH:. $(PY_RUN_CMD) python bin/create-leave-admin-and-claims.py $(args)

create-benefit-years: ## Create local benefit years data
	PYTHONPATH=$$PYTHONPATH:. $(PY_RUN_CMD) python bin/create-benefit-years.py $(args)

create-claim-with-payments-for-user: ## Create local API user with claims + payments (usable with payment status API)
	PYTHONPATH=$$PYTHONPATH:. $(PY_RUN_CMD) python bin/create_claim_with_payments_for_user.py $(args)

create-user: ## Create local API User
	PYTHONPATH=$$PYTHONPATH:. $(PY_RUN_CMD) python bin/create-user.py $(args)

console: ## Start interactive Python console
	$(PY_RUN_CMD) python3 -i -m massgov.pfml.tool.console.interactive

deps: ## Install dependencies
	$(POETRY_CMD) install --no-root --extras "api-only-dependencies"

deps-check: ## Check dependencies for vulnerabilities using Safety
	$(PY_RUN_CMD) safety check --full-report --ignore=42050 --ignore=42194

distclean: ## Remove all artifacts that can be regenerated
distclean: clean clean-node clean-venv
	rm -f jwks.json
	rm -rf dor_mock/ eligibility_export/ fineos_daily_mock/

dor-generate: ## Generate fake DOR data
	$(PY_RUN_CMD) dor-generate --folder dor_mock --count 1000 $(DECODE_LOG)

dor-generate-for-update: ## Generate fake update DOR data (mutation of subset of data from `make dor-generate`)
	$(PY_RUN_CMD) dor-generate --folder dor_mock --count 1000 --update $(DECODE_LOG)

fineos-update-xsds:
	$(PY_RUN_CMD) fineos-update-xsds $(DECODE_LOG)

fineos-daily-generate: ## Generate fake FINEOS employee extract
	$(PY_RUN_CMD) fineos-daily-generate --folder fineos_daily_mock --count 1000 $(DECODE_LOG)

fineos-import-employee-updates: ## Generate fake FINEOS employee extract
	FINEOS_FOLDER_PATH=fineos_daily_mock FINEOS_AWS_IAM_ROLE_ARN="arn" FINEOS_AWS_IAM_ROLE_EXTERNAL_ID="1" $(PY_RUN_CMD) fineos-import-employee-updates $(DECODE_LOG)

fineos-import-la-units: ## Import fake FINEOS leave admin org unit extract
	FINEOS_FOLDER_PATH=fineos_daily_mock FINEOS_AWS_IAM_ROLE_ARN="arn" FINEOS_AWS_IAM_ROLE_EXTERNAL_ID="1" $(PY_RUN_CMD) fineos-import-la-units $(DECODE_LOG)

dor-import: ## Run a DOR import using fake data (see dor-generate)
	FOLDER_PATH=dor_mock $(PY_RUN_CMD) dor-import $(DECODE_LOG)

mfa-lockout-resolution: ## Disable MFA on a user's account
	$(PY_RUN_CMD) mfa-lockout-resolution $(args) $(DECODE_LOG)

load-employers-to-fineos: ## Send employers from our database to the FINEOS API
	$(PY_RUN_CMD) load-employers-to-fineos $(DECODE_LOG)

fineos-eligibility-feed-export: ## Run an eligibility feed export
	mkdir -p eligibility_export/absence-eligibility/upload
	OUTPUT_DIRECTORY_PATH=eligibility_export FINEOS_AWS_IAM_ROLE_ARN="arn" FINEOS_AWS_IAM_ROLE_EXTERNAL_ID="1" $(PY_RUN_CMD) fineos-eligibility-feed-export $(DECODE_LOG)

dua-import-employee-demographics:
	$(PY_RUN_CMD) dua-import-employee-demographics $(args) $(DECODE_LOG)

dua-import-employer:
	$(PY_RUN_CMD) dua-import-employer $(args) $(DECODE_LOG)

dua-import-employer-unit:
	$(PY_RUN_CMD) dua-import-employer-unit $(args) $(DECODE_LOG)

dua-generate-and-send-employee-request-file:
	$(PY_RUN_CMD) dua-generate-and-send-employee-request-file $(args) $(DECODE_LOG)

dua-generate-and-send-employer-request-file:
	$(PY_RUN_CMD) dua-generate-and-send-employer-request-file $(args) $(DECODE_LOG)

sftp-tool:
	$(PY_RUN_CMD) sftp-tool $(args) $(DECODE_LOG)

pub-payments-process-fineos:
	$(PY_RUN_CMD) pub-payments-process-fineos --steps ALL $(DECODE_LOG)

pub-claimant-address-validation:
	$(PY_RUN_CMD) pub-claimant-address-validation --steps ALL $(DECODE_LOG)

pub-payments-create-pub-files:
	$(PY_RUN_CMD) pub-payments-create-pub-files --steps ALL $(DECODE_LOG)

pub-payments-process-pub-returns:
	$(PY_RUN_CMD) pub-payments-process-pub-returns --steps ALL $(DECODE_LOG)

pub-payments-process-snapshot:
	$(PY_RUN_CMD) pub-payments-process-snapshot --steps ALL $(DECODE_LOG)

pub-payments-mock-generate:
	$(PY_RUN_CMD)  pub-payments-mock-generate $(DECODE_LOG)

pub-payments-backfill-data:
	$(PY_RUN_CMD)  pub-payments-backfill-data --steps run-pei-line-item-backfill $(DECODE_LOG)

pub-payments-process-1099-documents:
	$(PY_RUN_CMD) pub-payments-process-1099-documents --steps ALL $(DECODE_LOG)

delegated-payment-audit-rejects-generate:
	mkdir -p mock_payment_rejects_files
	$(PY_RUN_CMD) delegated-payment-audit-rejects-generate --folder mock_payment_rejects_files $(DECODE_LOG)

delegated-payment-eft-response-generate:
	mkdir -p mock_payment_eft_response
	$(PY_RUN_CMD) delegated-payment-eft-response-generate --skiprate 50 --folder mock_payment_eft_response $(DECODE_LOG)

delegated-payment-check-response-generate:
	mkdir -p mock_payment_check_response
	$(PY_RUN_CMD) delegated-payment-check-response-generate --folder mock_payment_check_response $(DECODE_LOG)

fineos-import-iaww:
	$(PY_RUN_CMD) fineos-import-iaww --steps ALL $(DECODE_LOG)

ecr-login: ## Login to ECR for Docker
	@echo "Authenticating Docker with ECR"
	aws ecr get-login-password --region 'us-east-1' | \
	docker login --username AWS --password-stdin 498823821309.dkr.ecr.us-east-1.amazonaws.com

pre-commit:
	$(PY_RUN_CMD) isort --atomic --apply $(args)
	$(PY_RUN_CMD) black $(args)
ifdef flake_args
	$(PY_RUN_CMD) flake8 $(flake_args)
endif
ifdef mypy_args
	$(PY_RUN_CMD) mypy $(mypy_args)
endif

format: ## Format code
	$(PY_RUN_CMD) isort --atomic --apply
	$(PY_RUN_CMD) black .

format-check: ## Check format of code
	$(PY_RUN_CMD) isort --atomic --check-only
	$(PY_RUN_CMD) black . --check

# Allow command to be run with max={num}, where {num} is the number of recent commits to include.
# e.g. max=0 is only 'dirty' file changes, max=1 includes changes from the latest commit.
format-changed: max := 0
format-changed: FILES := $(shell [ "$(GIT_REPO_AVAILABLE)" = "true" ] && { \
	git diff --name-only --relative HEAD~$(max); \
	git diff --name-only --staged --relative HEAD~$(max); \
	git ls-files --other --exclude-standard HEAD~$(max);} | \
	grep \\.py | uniq)
format-changed: ## Format changed files, $max var determines number of commits to compare
	$(PY_RUN_CMD) isort --atomic --apply $(FILES)
	$(PY_RUN_CMD) black $(FILES)

generate-wagesandcontributions: ## Generate fake WagesAndContributions data
	$(PY_RUN_CMD) generate-wagesandcontributions --employer_fein=$(employer_fein) --employee_ssn=$(employee_ssn)

init: ## Initialize project to run locally
init: build deps jwks.json init-db

init-db: ## Initialize local DB
init-db: start-db db-upgrade db-create-users

jwks.json: ## Generate a local JSON Web Key Set to use for local API Authentication
	$(PY_RUN_CMD) python3 -W ignore bin/create-jwks.py
	$(PY_RUN_CMD) python3 -W ignore -m json.tool $@ > /dev/null 2>&1 || (echo "$@ is not valid JSON" && exit 1)

jwt: ## Generate a JSON Web Token for $auth_id signed by locally generated JWKS
jwt: jwks.json
	$(PY_RUN_CMD) python3 -W ignore bin/create-jwt.py ./jwks.json $(auth_id)

# A flake8 output format that is compatible with GitHub Actions to annotate PRs. A full repository path must be output
# so the path is prefixed with `api/`.
# See https://help.github.com/en/actions/reference/workflow-commands-for-github-actions
ifdef CI
 FLAKE8_FORMAT := '::warning file=api/%(path)s,line=%(row)d,col=%(col)d::%(path)s:%(row)d:%(col)d: %(code)s %(text)s'
 MYPY_FLAGS := --no-pretty
 MYPY_POSTPROC := | perl -pe "s/^(.+):(\d+):(\d+): error: (.*)/::warning file=api\/\1,line=\2,col=\3::\4/"
 SPECTRAL_POSTPROC := --format=text | perl -pe "s/^\/tmp\/(.+):(\d+):(\d+) (error|warning) (.*)/::warning file=api\/\1,line=\2,col=\3::\4 \5/"
else
 FLAKE8_FORMAT := default
endif

lint-changed: max := 0
lint-changed: FILES := $(shell [ "$(GIT_REPO_AVAILABLE)" = "true" ] && { \
	git diff --name-only --relative HEAD~$(max); \
	git diff --name-only --staged --relative HEAD~$(max); \
	git ls-files --other --exclude-standard HEAD~$(max);} | \
	grep -E '^(massgov|tests|bin)/.*\.py' | sort -u)
lint-changed: FILES_MYPY := $(shell echo $(FILES) | tr " " "\n" | grep -E '^(massgov|bin)/')
lint-changed: ## Lint changed files, $max var determines number of commits to compare
	$(PY_RUN_CMD) flake8 --format=$(FLAKE8_FORMAT) $(FILES)
	$(PY_RUN_CMD) mypy $(MYPY_FLAGS) $(FILES_MYPY) $(MYPY_POSTPROC)

lint: ## Run linting
lint: lint-spectral lint-py db-check-model-parity

lint-py: ## Run python linting
lint-py: lint-flake lint-mypy lint-poetry-version

lint-poetry-version: ## Check poetry version
	grep --quiet 'lock-version = "1.1"' poetry.lock

lint-flake: ## Run flake8
	$(PY_RUN_CMD) flake8 --format=$(FLAKE8_FORMAT) massgov tests bin

lint-mypy: ## Run mypy
	$(PY_RUN_CMD) mypy $(MYPY_FLAGS) massgov bin $(MYPY_POSTPROC)

lint-security: ## Run security linting
	$(PY_RUN_CMD) bandit -r . --number 3 --skip B101 -ll

lint-spectral: ## Run OpenAPI Spec linting
	docker run --rm --tty --cap-drop=ALL --network=none --read-only --volume=$(PWD):/tmp:ro \
           stoplight/spectral:6 lint /tmp/$(OPEN_API_PATH) --ruleset /tmp/.spectral.yaml $(SPECTRAL_POSTPROC)

login: start ## Start shell in running container
	docker exec -it $(APP_NAME) bash

login-root: start ## Start root shell in running container
	docker exec --user 0 -it $(APP_NAME) bash

login-db: ## Start psql with project environment variables
	PGPASSWORD=$$DB_PASSWORD psql --host=$$DB_HOST --username=$$DB_USERNAME $$DB_NAME

login-db-admin: ## Start psql with project environment variables and admin user
	PGPASSWORD=$$DB_ADMIN_PASSWORD psql --host=$$DB_HOST --username=$$DB_ADMIN_USERNAME $$DB_NAME

logs: start ## View API logs
	docker-compose logs --follow --no-color $(APP_NAME) $(DECODE_LOG)


logs-local: ## Run start-local, with API logs
logs-local: start-local
	docker-compose logs --follow --no-color $(APP_NAME) $(DECODE_LOG)

logs-db: start ## View DB logs
	docker-compose logs --follow mass-pfml-db

process-tpa-csv: ## Creates mailable CSVs per email address in input file
	$(PY_RUN_CMD) python bin/process-tpa-csv.py \
		--aws-access-key-id=$(aws-access-key-id) \
		--aws-secret-access-key=$(aws-secret-access-key) \
		--aws-session-token=$(aws-session-token) \
		--input=$(input) \
		--output-dir=$(output-dir) \
		--url-expiration-days=$(url-expiration-days)

psql: login-db

start: ## Start all containers
start: jwks.json
	docker-compose up --detach

start-local: ## Start all containers using a cognito instance, in order to match local-to-local development with portal
start-local:
	docker-compose --env-file .env.local up --detach

start-db: ## Start DB container
	docker-compose up --detach mass-pfml-db

stop: ## Stop all running containers
	docker-compose down

build-and-publish: ## Build and publish release image
build-and-publish: api-image-build api-image-publish

build-and-publish-pdf-api: ## Build and publish release image for PDF API
build-and-publish-pdf-api: pdf-api-image-build pdf-api-image-publish

api-image-build: ## Build release image
	docker build \
		--tag $(APP_NAME):latest \
		--tag $(APP_NAME):$(IMAGE_TAG) \
		--target app \
		--build-arg RUN_USER=container \
		--build-arg RUN_UID=4000 \
		.

pdf-api-image-build: ## Build release pdf-api image
	docker build \
		--tag $(APP_NAME)-pdf:latest \
		--tag $(APP_NAME)-pdf:$(IMAGE_TAG) \
		--target final \
		.

release-start-api: jwks.json ## starts api container without an attached database
	docker-compose --file docker-compose.yml --file docker-compose.release.yml up --detach

release-stop-api:
	docker-compose --file docker-compose.yml --file docker-compose.release.yml down

pre-flight-test: db-upgrade db-create-users release-start-api health-check

# Since we have a time-based tag INFO_TAG, tagging and pushing are usually best
# to be done together, but you could tag then later push by setting INFO_TAG
# directly
api-image-publish: ## Tag and push release
api-image-publish: ecr-login api-image-tag api-image-push

pdf-api-image-publish: ## Tag and push pdf-api release
pdf-api-image-publish: ecr-login pdf-api-image-tag pdf-api-image-push

api-image-push: ## Push release image to the registry
	docker push $(DOCKER_REGISTRY)/$(DOCKER_REPO):$(IMAGE_TAG)
	docker push $(DOCKER_REGISTRY)/$(DOCKER_REPO):$(INFO_TAG)

pdf-api-image-push: ## Push release pdf-api image to the registry
	docker push $(DOCKER_REGISTRY)/$(DOCKER_PDF_REPO):$(IMAGE_TAG)
	docker push $(DOCKER_REGISTRY)/$(DOCKER_PDF_REPO):$(INFO_TAG)

api-image-tag: ## Tag release image for registry
	docker tag $(APP_NAME):$(IMAGE_TAG) $(DOCKER_REGISTRY)/$(DOCKER_REPO):$(IMAGE_TAG)
	docker tag $(APP_NAME):$(IMAGE_TAG) $(DOCKER_REGISTRY)/$(DOCKER_REPO):$(INFO_TAG)

pdf-api-image-tag: ## Tag release pdf-api image for registry
	docker tag $(APP_NAME)-pdf:$(IMAGE_TAG) $(DOCKER_REGISTRY)/$(DOCKER_PDF_REPO):$(IMAGE_TAG)
	docker tag $(APP_NAME)-pdf:$(IMAGE_TAG) $(DOCKER_REGISTRY)/$(DOCKER_PDF_REPO):$(INFO_TAG)

runcmd: ## Run poetry command
	$(PY_RUN_CMD) $(cmd)

health-check: # The second parameter is the number of retries (each followed by
		  # a second of wait) until a state is determined by the docker daemon
	./bin/check_container_health.sh 60

run: ## Run docker-compose
run: start logs

run-native: ## Start API server directly
run-native: jwks.json
	poetry run python -m massgov.pfml.api $(DECODE_LOG)

db-check-model-parity: ## Ensure application models are in sync with the database
	$(PY_RUN_CMD) db-check-model-parity

db-create-users: ## Create database users
	$(PY_RUN_CMD) db-admin-create-db-users $(DECODE_LOG)

db-upgrade: ## Apply pending migrations to db
	$(PY_RUN_CMD) db-migrate-up  $(DECODE_LOG)

db-downgrade: ## Rollback last migration in db
	$(PY_RUN_CMD) db-migrate-down  $(DECODE_LOG)

db-downgrade-all: ## Rollback all migrations
	$(PY_RUN_CMD) db-migrate-down-all $(DECODE_LOG)

db-dump-schema: ## Print current DB schema
	PGPASSWORD=$$DB_PASSWORD pg_dump --host=$$DB_HOST --username=$$DB_USERNAME $$DB_NAME --schema-only $(args)

alembic_config := ./massgov/pfml/db/migrations/alembic.ini
alembic_cmd := $(PY_RUN_CMD) alembic --config $(alembic_config)

db-migrate-create: ## Create new migration based on model changes, requires $MIGRATE_MSG
db-migrate-create: check-migrate-msg
	$(alembic_cmd) revision --autogenerate -m "$(MIGRATE_MSG)"

db-migrate-current: ## Show current revision for a database
	$(alembic_cmd) current $(args)

db-migrate-history: ## Show migration history
	$(alembic_cmd) history $(args)

db-migrate-heads: ## Show migrations marked as a head
	$(alembic_cmd) heads $(args)

MIGRATE_MERGE_MSG := Merge multiple heads
db-migrate-merge-heads: ## Create a new migration that depends on all existing `head`s
	$(alembic_cmd) merge heads -m "$(MIGRATE_MERGE_MSG)" $(args)

db-migrate-run: ## Run alembic with $args
	$(alembic_cmd) $(args)

db-recreate: ## Destroy current DB, setup new one
db-recreate: clean-docker-volumes init-db

check-migrate-msg:
ifndef MIGRATE_MSG
	$(error MIGRATE_MSG is undefined)
endif

define run_tests
	$(PY_RUN_CMD) pytest $(1)
endef

ifdef CI
 XDIST := -n auto --dist=loadfile --max-worker-restart=0 -x
else
 XDIST :=
endif

test: ## Run tests, set $args to pass flags to `pytest`
	$(call run_tests, $(args))

test-coverage: ## Run tests run
	$(PY_RUN_CMD) coverage run --branch --source=massgov -m pytest $(XDIST) $(args)
	$(PY_RUN_CMD) coverage report
	$(PY_RUN_CMD) coverage lcov

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

test-coverage-combine: ## Combine coverage report for CI
	mv .coverage .coverage.api
	$(PY_RUN_CMD) coverage combine --keep .coverage.api

test-integration: ## Run just integration tests, set $args to pass flags to `pytest`
	$(call run_tests,-m integration $(args))

test-unit: ## Run just unit tests, set $args to pass flags to `pytest`
	$(call run_tests,-m 'not integration' $(args))

define run_test_watch
	$(PY_RUN_CMD) pytest-watch -- $(1)
endef

test-watch: ## Watch and run tests on file changes, set $args to pass flags to `pytest`
	$(call run_test_watch, $(args))

test-watch-changed: ## Watch and run `make test-changed` on file changes
	$(PY_RUN_CMD) pytest-watch --runner "make test-changed"

test-watch-focus: ## Watch and run tests decorated with `@pytest.mark.dev_focus` on file changes
	$(call run_test_watch,-m dev_focus $(args))

start-release: ## Creates a new release series. Increments the API's minor version number.
	pushd ../bin/ci && poetry run scripted-releases --app api start-release $(args) && popd

update-release: ## Updates an in-progress release series. Increments the API's RC number.
	pushd ../bin/ci && poetry run scripted-releases --app api update-release $(args) && popd

finalize-release: ## Marks a release series as approved to go to prod. Enables hotfixes; disables updates.
	pushd ../bin/ci && poetry run scripted-releases --app api finalize-release $(args) && popd

hotfix: ## Alters a release series that already went to prod. Increments the API's patch version number.
	pushd ../bin/ci && poetry run scripted-releases --app api hotfix $(args) && popd

major-release: ## Creates a new release series. Increments the API's MAJOR version number.
	pushd ../bin/ci && poetry run scripted-releases --app api major-release $(args) && popd

API_PATHS := . ../infra/api ../infra/ecs-tasks ../infra/env-shared ../infra/modules/ecs_task_scheduler ../infra/modules/s3_ecs_trigger
release-notes: refs=origin/deploy/api/stage..origin/main
release-notes: ## Generate API release notes for $refs (defaults between stage and test)
	@git log --pretty='format: * %s' $(refs) -- $(API_PATHS) | \
	sed -E 's;^ \* \[*([A-Za-z]{2,}-[0-9]+)[] :]*(.*); \* [\1](https://lwd.atlassian.net/browse/\1): \2;' | \
	sed -E 's;\(#([0-9]+)\);([#\1](https://github.com/EOLWD/pfml/pull/\1));'

release-list: refs=origin/deploy/api/stage..origin/main
release-list: ## Generate comma-separated list of ticket ids for $refs
	@git log --pretty='format: %s' $(refs) -- $(API_PATHS) | \
	grep --extended-regexp --only-matching '[A-Za-z]{2,}-[0-9]+' | \
	tr '\n' ',' | sed 's/,$$//'


API_RELEASE_BRANCHES := $(addprefix origin/, main deploy/api/stage deploy/api/prod deploy/api/performance deploy/api/training deploy/api/uat deploy/api/breakfix deploy/api/cps-preview deploy/api/long deploy/api/trn2 deploy/api/infra-test)
where-ticket: ## Search release branches for $ticket
	@for b in $(API_RELEASE_BRANCHES); do echo "## $$b ##"; \
		git --no-pager log --oneline --decorate --grep=$(ticket) $$b; \
		echo ""; \
	done

whats-released: ## List latest commit on release branches
	@for branch in $(API_RELEASE_BRANCHES); do echo "## $$branch ##"; \
		echo " * Closest tag: $$(git describe --tags --match api/v* $$branch)"; \
		echo " * Latest commit: $$(git --no-pager log --oneline --decorate --color -n 1 $$branch)"; \
		echo ""; \
	done

whats-released-short: ## List latest version tag on release branches
	@for branch in $(API_RELEASE_BRANCHES); do \
		echo " * $$branch: $$(git describe --tags --match api/v* $$branch)"; \
	done

update-poetry-lock-hash: ## Update metadata.content-hash in poetry.lock
	$(POETRY_CMD) lock --no-update

experian-generate-layouts: ## Fetch supported layouts from Experian server
	$(PY_RUN_CMD) ./bin/experian/generate-layouts.py > massgov/pfml/experian/address_validate_soap/layouts.py

help: ## Displays this help screen
	@grep -Eh '^[[:print:]]+:.*?##' $(MAKEFILE_LIST) | \
	sort -d | \
	awk -F':.*?## ' '{printf "\033[36m%s\033[0m\t%s\n", $$1, $$2}' | \
	column -t -s "$$(printf '\t')"
	@echo ""
	@echo "APP_NAME=$(APP_NAME)"
	@echo "INFO_TAG=$(INFO_TAG)"
	@echo "RUN_CMD_OPT=$(RUN_CMD_OPT)"
	@echo "GIT_REPO_AVAILABLE=$(GIT_REPO_AVAILABLE)"
	@echo "IMAGE_TAG=$(IMAGE_TAG)"
	@echo "RUN_UID=$(RUN_UID)"
	@echo "RUN_USER=$(RUN_USER)"
	@echo "SHELL=$(SHELL)"
	@echo "MAKE_VERSION=$(MAKE_VERSION)"
	@echo "COGNITO_USER_POOL_KEYS_URL=$(COGNITO_USER_POOL_KEYS_URL)"
