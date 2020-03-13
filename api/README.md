# Massachusetts PFML API

This is the API for the Massachusetts Paid Family and Medical Leave program.

## Setup

Install at least Python 3.8.
[pyenv](https://github.com/pyenv/pyenv#installation) is one popular option for
installing Python.

After installing and activating the right version of Python, install
[poetry](https://python-poetry.org/docs/#installation).

Then:
```sh
make deps
```

Alternatively, without install Python or Poetry, can use Docker:
```sh
make docker-build
```

## Run

```sh
make run-dev
```

Alternatively using Docker:
```sh
make docker-run
```

## Try it out

A UI is available at http://localhost:1550/v1/ui/

The spec is available at http://localhost:1550/v1/openapi.json (JSON) or
http://localhost:1550/v1/openapi.yaml (YAML).

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
