# Massachusetts PFML API

This is the API for the Massachusetts Paid Family and Medical Leave program.

## Setup

### Docker

Docker can be used for a local development environment. It sets up Python,
Poetry and installs development dependencies automatically.

#### Configuration

Environment variables for the app are under `services.mass-pfml-api.environment`
in the `docker-compose.yml` file.

If you want to run various Python and development `make` commands (linting,
tests, etc.) from the host, but have them run in the Docker environment, you
should set `PY_RUN_CMD_OPT` to either `DOCKER_RUN` or `DOCKER_EXEC`, see the
option descriptions in the `Makefile`.

If you intend to login to the Docker environment and run development `make`
commands, you can leave `PY_RUN_CMD_OPT` on it's default of `POETRY`.

If you will mix and match running things, well, you'll have to juggle
`PY_RUN_CMD_OPT` yourself, e.g., `PY_RUN_CMD_OPT=POETRY make lint`. Might in the
future add some auto-detection of if we are running inside the container or not.

#### Run

Start the API
```sh
make start
```

Login to the container, where you can run development tools
```sh
make login
```

Rebuild after code or dependency change
```sh
make build
```

Stop running docker containers
```sh
make stop
```

### Native

To setup a development environment outside of Docker requires installing a few
things.

#### Dependencies

- Install at least Python 3.8.
  [pyenv](https://github.com/pyenv/pyenv#installation) is one popular option for
  installing Python.
- After installing and activating the right version of Python, install
  [poetry](https://python-poetry.org/docs/#installation).
- Then run `make deps` to install Python dependencies and development tooling.

You should now be set up to run things natively.

## Try it out

A UI is available at http://localhost:1550/v1/ui/

The spec is available at http://localhost:1550/v1/openapi.json (JSON) or
http://localhost:1550/v1/openapi.yaml (YAML).

## Tests

``` sh
make test
```

[pytest](https://docs.pytest.org) is our test runner, which is simple but
powerful. If you are new to pytest, reading up on how [fixtures
work](https://docs.pytest.org/en/latest/fixture.html) in particular might be
helpful as it's one area that is a bit different than is common with other
runners (and languages).

### During Development

While working on a part of the system, you may not be interested in running the
entire test suite all the time. To just run the test impacted by the changes
made since they last ran, you can use:

``` sh
make test-changed
```

Note that it will run the entire test suite the first time that command is run
to collect which source files touch which tests, subsequent runs should only run
the tests that need to run.

And instead of running that command manually, you can kick off a process to
automatically run the tests when files change with:

``` sh
make test-watch
```

### Running Migrations

Pre-requisite: Database needs to be up and running
```
$ make run
```

Auto-generate migration files from model changes:
```
$ docker-compose run --no-deps mass-pfml-api sh -c 'poetry run alembic -c ./massgov/pfml/db/alembic.ini revision --autogenerate -m "<brief description of change>"'
```

Apply pending migrations to db
```
$ make db-upgrade
```

Rollback last migration to db:
```
$ make db-downgrade
```

Rollback all migrations to db:
```
$ make db-downgrade-all
```

## Directory Structure

```
.
├── massgov
│   └── pfml
│       └── api         Application code
├── mock                Mock data generators
├── tests
│   └── api             Application tests
├── Dockerfile          Multi-stage Docker build file for project
├── docker-compose.yml  Config file for docker-compose tool, used for local development
├── openapi.yaml        API specification
├── pyproject.toml      Python project configuration file
└── setup.cfg           Python config for tools that don't support pyproject.toml yet
```
