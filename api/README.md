# Massachusetts PFML API

This is the API for the Massachusetts Paid Family and Medical Leave program.

## Setup

Docker is used for local development environment.

### Dependencies

Poetry is used to manage python library dependencies:
- Install at least Python 3.8.
[pyenv](https://github.com/pyenv/pyenv#installation) is one popular option for installing Python.
- After installing and activating the right version of Python, install
[poetry](https://python-poetry.org/docs/#installation).

### Configuration

Environment variables for the app are under `services.mass-pfml-api.environment` in the `dokcker-compose` file.

### Run

Start the API

```sh
make run
```

Rebuild after code or dependency change
```sh
make build
```

Stop running docker containers
```sh
make stop
```

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

## Directory Structure

```
.
├── massgov
│   └── pfml
│       └── api      Application code
├── mock             Mock data generators
├── tests
│   └── api          Application tests
├── openapi.yaml     API specification
├── pyproject.toml   Python project configuration file
└── setup.cfg        Python config for tools that don't support pyproject.toml yet
```
