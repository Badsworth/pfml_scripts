# Massachusetts PFML API

This is the API for the Massachusetts Paid Family and Medical Leave program.

* [Docker Developer Setup](#docker-developer-setup)
* [Running the Application (Docker)](#running-the-application-docker)
  * [Common commands](#common-commands)
  * [Running migrations](#running-migrations)
  * [Creating new migrations](#creating-new-migrations)
* [Native Developer Setup](#native-developer-setup)
* [Try it out](#try-it-out)
* [Tests](#tests)
* [Environment Configuration](#environment-configuration)
* [Directory Structure](#directory-structure)

## Docker Developer Setup

Docker is heavily recommended for a local development environment. It sets up Python,
Poetry and installs development dependencies automatically, and can create a full environment
including the API application and a backing database.

Follow instructions here to [install Docker](https://docs.docker.com/get-docker/) for your OS.

In a docker-centric environment, we support a couple different developer workflows:

|Start command from:|Container Lifetime|PY\_RUN\_CMD\_OPT|
|---|---|---|
|your host 🙋‍♀️|Long-running|DOCKER_EXEC|
|inside docker 🐳|Long-running|N/A|
|your host 🙋‍♀️|Single-use|DOCKER_RUN|
|Mixed|Mixed|Mixed|

<details><summary>Send commands from your host to a long-running container</summary>
<p>
If you want to re-use a docker application for various Python and development
 <code>make</code> commands (e.g. linting and testing), you should set
 <code>PY_RUN_CMD_OPT</code> to <code>DOCKER_EXEC</code>.

```sh
$ export PY_RUN_CMD_OPT=DOCKER_EXEC
$ make test
```
</p>
</details>

<details><summary>Log into a docker container to run commands</summary>
<p>If you intend to start a Docker environment and log into it like a remote server,
 you can leave <code>PY_RUN_CMD_OPT</code> alone and use <code>make login</code> instead.

```sh
$ make login
> make test
```
</p>
</details>

<details><summary>Start a new docker container for every command</summary>
<p>If you plan to run commands through temporary, single-use Docker containers, you
 should set your <code>PY_RUN_CMD_OPT</code> to <code>DOCKER_RUN</code>:

```sh
$ export PY_RUN_CMD_OPT=DOCKER_RUN
$ make test
```

Note that this will require more manual Docker memory cleanup.
</p>
</details>

<details><summary>Mix and Match</summary>
 <p>If you plan to mix and match things, you'll have to juggle <code>PY_RUN_CMD_OPT</code> yourself.

For example:

- running static lints outside of Docker with the default: <code>make lint</code>
- running tests inside of Docker after a <code>make start</code>: <code>PY_RUN_CMD_OPT=DOCKER_EXEC make test</code>

In the future, we may add some auto-detection to check if we are running inside the 
container or not.
</p>
</details>

## Running the Application (Docker)

#### Common commands

```
make start  # Start the API
make logs   # View API logs
make login  # Login to the container, where you can run development tools
make build  # Rebuild container and pick up new environment variables
make stop   # Stop all running containers
```

#### Running migrations

When you're first setting up your environment, ensure that migrations are run against your db so it has all the required tables.

```
$ make db-upgrade       # Apply pending migrations to db
$ make db-downgrade     # Rollback last migration to db
$ make db-downgrade-all # Rollback all migrations
```

#### Creating new migrations

If you've changed a python object model, auto-generate a migration file for the database and run it:

```
$ make db-migrate-create MIGRATE_MSG="<brief description of change>"
$ make db-upgrade
```

## Native Developer Setup

To setup a development environment outside of Docker, 
you'll need to install a few things.

#### Dependencies

- Install at least Python 3.8.
  [pyenv](https://github.com/pyenv/pyenv#installation) is one popular option for
  installing Python, or [asdf](https://asdf-vm.com/).
- After installing and activating the right version of Python, install
  [poetry](https://python-poetry.org/docs/#installation).
- Then run `make deps` to install Python dependencies and development tooling.

You should now be set up to run developer tooling natively, like linting. To run 
the application, set up a PostgreSQL database and see `docker-compose.yml` for 
environment variables needed.

## Try it out

Once your application is running, a UI is available at:

- [http://localhost:1550/v1/ui/](http://localhost:1550/v1/ui/)

The spec is available at:

- [http://localhost:1550/v1/openapi.json](http://localhost:1550/v1/openapi.json) (JSON) or
- [http://localhost:1550/v1/openapi.yaml](http://localhost:1550/v1/openapi.yaml) (YAML)

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

## Environment Configuration

Environment variables for the local app in the `docker-compose.yml` file.

```
services:
  ...
  mass-pfml-api:
    ...
    environment:
    - ENVIRONMENT=local
    - DB_URL=mass-pfml-db
    - ...
```

## Directory Structure

```
.
├── massgov
│   └── pfml
│       └── api                 Application code
│       └── db                  Migrations config
│       └── data-integrations
│           └── */lambda        Data ingestion lambda for an agency
│           └── */mock          Mock data generator for an agency
├── tests
│   └── api             Application tests
├── Dockerfile          Multi-stage Docker build file for project
├── docker-compose.yml  Config file for docker-compose tool, used for local development
├── openapi.yaml        API specification
├── pyproject.toml      Python project configuration file
└── setup.cfg           Python config for tools that don't support pyproject.toml yet
```
