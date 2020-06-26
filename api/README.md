# Massachusetts PFML API

This is the API for the Massachusetts Paid Family and Medical Leave program.

- [Docker Developer Setup](#docker-developer-setup)
- [Running the Application (Docker)](#running-the-application-docker)
  - [Common commands](#common-commands)
  - [Running migrations](#running-migrations)
  - [Creating new migrations](#creating-new-migrations)
- [Native Developer Setup](#native-developer-setup)
- [Try it out](#try-it-out)
- [Tests](#tests)
- [Environment Configuration](#environment-configuration)
- [Directory Structure](#directory-structure)

## Docker Developer Setup

Docker is heavily recommended for a local development environment. It sets up Python,
Poetry and installs development dependencies automatically, and can create a full environment
including the API application and a backing database.

Follow instructions here to [install Docker](https://docs.docker.com/get-docker/) for your OS.

In a docker-centric environment, we support a couple different developer workflows:

| Start command from: | Container Lifetime | PY_RUN_CMD_OPT |
| ------------------- | ------------------ | -------------- |
| your host 🙋‍♀️        | Long-running       | DOCKER_EXEC    |
| inside docker 🐳    | Long-running       | N/A            |
| your host 🙋‍♀️        | Single-use         | DOCKER_RUN     |
| Mixed               | Mixed              | Mixed          |

The default is `DOCKER_RUN` and should always just work™. But this spins up a
new container for every command, which can be slow. If you are working on the
API a lot, you may want to consider one of the alternative setups below and/or
the [Native Developer Setup](#native-developer-setup).

Some tasks will usually need to be run with `DOCKER_RUN` regardless of the
workflow used otherwise. Examples include generating an initial local JWKS
(`make jwks.json`) or running migrations (`make db-upgrade`).

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

Note this is the default setting.

</p>
</details>

<details><summary>Mix and Match</summary>
 <p>If you plan to mix and match things, you'll have to juggle <code>PY_RUN_CMD_OPT</code> yourself.

For example:

- running static lints outside of Docker with native developer setup: <code>PY_RUN_CMD_OPT=POETRY make lint</code>
- running tests inside of Docker after a <code>make start</code>: <code>PY_RUN_CMD_OPT=DOCKER_EXEC make test</code>

</p>
</details>

## Running the Application (Docker)

#### Common commands

```sh
make start    # Start the API
make logs     # View API logs
make login    # Login to the container, where you can run development tools
make login-db # Start a psql prompt in the container, where you can run SQL queries. requires make login.
make build    # Rebuild container and pick up new environment variables
make stop     # Stop all running containers
```

#### Running migrations

When you're first setting up your environment, ensure that migrations are run against your db so it has all the required tables.

```sh
$ make db-upgrade       # Apply pending migrations to db
$ make db-downgrade     # Rollback last migration to db
$ make db-downgrade-all # Rollback all migrations
```

#### Creating new migrations

If you've changed a python object model, auto-generate a migration file for the database and run it:

```sh
$ make db-migrate-create MIGRATE_MSG="<brief description of change>"
$ make db-upgrade
```

#### Multi-head situations

Alembic migrations form an ordered history, with each migration having at least
one parent migration as specified by the `down_revision` variable. This can be
visualized by:

```sh
make db-migrate-history
```

When multiple migrations are created that point to the same `down_revision` a
branch is created, with the tip of each branch being a "head". The above history
command will show this, but a list of just the heads can been retrieved with:

```sh
make db-migrate-heads
```

CI/CD runs migrations to reach the "head". When there are multiple, Alembic
can't resolve which migrations need to be run. If you run into this error,
you'll need to fix the migration branches/heads before merging to `master`.

If the migrations don't depend on each other, which is likely if they've
branched, then you can just run:

``` sh
make db-migrate-merge-heads
```

Which will create a new migration pointing to all current "head"s, effectively
pulling them all together.

When branched migrations do need to happen in a defined order, then manually
update the `down_revision` of one that should happen second to reference to the
migration that should happen first.

## Native Developer Setup

To setup a development environment outside of Docker, you'll need to install a
few things.

#### Dependencies

- Install at least Python 3.8.
  [pyenv](https://github.com/pyenv/pyenv#installation) is one popular option for
  installing Python, or [asdf](https://asdf-vm.com/).
- After installing and activating the right version of Python, install
  [poetry](https://python-poetry.org/docs/#installation).
- Then set `PY_RUN_CMD_OPT` to `POETRY` in your development environment.
- Then run `make deps` to install Python dependencies and development tooling.

You should now be set up to run developer tooling natively, like linting. To run
the application, set up a PostgreSQL database and see `docker-compose.yml` for
environment variables needed.

## Try it out

Once your application is running, a UI is available at:

- [http://localhost:1550/v1/docs/](http://localhost:1550/v1/docs/)

The spec is available at:

- [http://localhost:1550/v1/openapi.json](http://localhost:1550/v1/openapi.json) (JSON) or
- [http://localhost:1550/v1/openapi.yaml](http://localhost:1550/v1/openapi.yaml) (YAML)

### Getting local authentication credentials

In order to make requests to the API, an authentication token must be included.
Currently this is a JWT set in the `Authorization` HTTP header. A JWT signed by
a locally generated JWK can be created for a user via:

```sh
make jwt auth_id=<active_directory_id of a user record>
```

Currently the JWT expires after a day, but we may tweak the lifetime for
convenience at some point.

If a user doesn't already exist, can create a random user in the database with:

```sh
make create-user
```

Which will print something like:

```
{'user_id': '548c9e28-3d72-4c5c-96e7-4a77f3c37041',
 'active_directory_id': '33f965ad-0150-4c5b-a3a6-86bbd5df1a26',
 'email_address': 'gfarmer@lewis.com',
 'consented_to_data_sharing': False}
```

The `active_directory_id` field is what is needed to generate a JWT. For the
example above, it would be:

```sh
make jwt auth_id=33f965ad-0150-4c5b-a3a6-86bbd5df1a26
```

Which will print something like:

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE1OTI0OTQxOTIsInN1YiI6IjMzZjk2NWFkLTAxNTAtNGM1Yi1hM2E2LTg2YmJkNWRmMWEyNiJ9.KMze0GfJ9cQ10e9G27vcOgn3nBiqhXxxtCBZYIgScFo
```

That value should be included as a bearer token in the `Authorization` header of
requests.

On the documentation pages mentioned in the section above, click the "Authorize"
button and paste the above value. After that every request sent from the docs
page will be authenticated with that token.

For individual requests via `curl` or similar:

```sh
curl -v --header "Authorization: Bearer <big jwt string above>" http://localhost:1550/v1/users/current
```

## Tests

```sh
make test
```

[pytest](https://docs.pytest.org) is our test runner, which is simple but
powerful. If you are new to pytest, reading up on how [fixtures
work](https://docs.pytest.org/en/latest/fixture.html) in particular might be
helpful as it's one area that is a bit different than is common with other
runners (and languages).

To pass arguments to `pytest` through `make test` you can set the `args`
variable. For example, to run only the tests in `test_user.py`:

```sh
make test args=tests/api/test_users.py
```

To run only a single test:

```sh
make test args=tests/api/test_users.py::test_users_get
```

To pass multiple arguments:

```sh
make test args="-x tests/api/test_users.py"
```

For a more complete description of the various ways you can select which test
cases to run or various behaviors that can be turned on, [refer to the pytest
docs](https://docs.pytest.org/en/latest/usage.html).

### During Development

While working on a part of the system, you may not be interested in running the
entire test suite all the time. To just run the test impacted by the changes
made since they last ran, you can use:

```sh
make test-changed
```

Note that it will run the entire test suite the first time that command is run
to collect which source files touch which tests, subsequent runs should only run
the tests that need to run.

And instead of running that command manually, you can kick off a process to
automatically run the tests when files change with:

```sh
make test-watch
```

## Environment Configuration

Environment variables for the local app in the `docker-compose.yml` file.

```yaml
services:
  ...
  mass-pfml-api:
    ...
    environment:
    - ENVIRONMENT=local
    - DB_HOST=mass-pfml-db
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
