# Massachusetts PFML API

This is the API for the Massachusetts Paid Family and Medical Leave program. See [this Confluence page](https://lwd.atlassian.net/wiki/spaces/API/pages/227770663/Paid+Leave+API) for a technical overview.

1. [Getting Started](#getting-started)
    1. [Quickstart](#quickstart)
    2. [Setup Your Development Environment](#setup-your-development-environment)
        1. [(Preferred) Docker + GNU Make](#preferred-docker--gnu-make)
        2. [Native Developer Setup](#native-developer-setup)
    3. [Development Workflow](#development-workflow)
2. [How it works](#how-it-works)
    1. [Key Technologies](#key-technologies)
    2. [Request operations](#request-operations)
    3. [Authentication](#authentication)
    4. [Authorization](#authorization)
3. [Running the Application (Docker)](#running-the-application-docker)
    1. [Initializing dependencies](#initializing-dependencies)
    2. [Common commands](#common-commands)
    3. [Managing the container environment](#managing-the-container-environment)
    4. [Running migrations](#running-migrations)
    5. [Creating new migrations](#creating-new-migrations)
    6. [Multi-head situations](#multi-head-situations)
4. [Try it out](#try-it-out)
    1. [Getting local authentication credentials](#getting-local-authentication-credentials)
    2. [Seed your database](#seed-your-database)
5. [Tests](#tests)
    1. [During Development](#during-development)
6. [Managing dependencies](#managing-dependencies)
    1. [poetry.lock conflicts](#poetry.lock-conflicts)
7. [Environment Configuration](#environment-configuration)
8. [How deploys work](#how-deploys-work)
9. [Monitoring and Alerting](#monitoring-and-alerting)
10. [Releases](#releases)
11. [Directory Structure](#directory-structure)

**You may also be interested in:**

- [Setting up project tooling](../README.md)
- [Development practices](../docs/contributing.md)
- [Adding fields and validations](../docs/api/fields-and-validations.md)
- [Additional API-specific documentation](../docs/api/)

## Getting Started

### Quickstart

0. Install [Docker](https://docs.docker.com/get-docker)
1. `cd pfml/api` (or otherwise move to this directory)
2. `make init`
3. `make start`
4. Navigate to the Swagger UI at [http://localhost:1550/v1/docs/](http://localhost:1550/v1/docs/)
5. [Setup local authentication](#getting-local-authentication-credentials)
6. Review documentation in `/docs`, especially [contributing.md](/docs/contributing.md) for guidelines on how to contribute code

### Setup Your Development Environment

You can set up your development environment in one of the following ways:

1. (Preferred) Docker + GNU Make
2. Native developer setup: Install dependencies directly on your OS

#### (Preferred) Docker + GNU Make

Docker is heavily recommended for a local development environment. It sets up Python,
Poetry and installs development dependencies automatically, and can create a full environment
including the API application and a backing database.

Follow instructions here to [install Docker](https://docs.docker.com/get-docker/) for your OS.

In a docker-centric environment, we support a couple different developer workflows:

| Start command from: | Container Lifetime | RUN_CMD_OPT |
| ------------------- | ------------------ | ----------- |
| your host 🙋‍♀️        | Long-running       | DOCKER_EXEC |
| inside docker 🐳    | Long-running       | N/A         |
| your host 🙋‍♀️        | Single-use         | DOCKER_RUN  |
| Mixed               | Mixed              | Mixed       |

The default is `DOCKER_RUN` and should always just work™. But this spins up a
new container for every command, which can be slow. If you are working on the
API a lot, you may want to consider one of the alternative setups below and/or
the [Native Developer Setup](#native-developer-setup).

**Note: Some tasks, including initial setup, will usually need to be run with `DOCKER_RUN`** regardless of the
workflow used otherwise. Examples include generating an initial local JWKS
(`make jwks.json`) or running migrations (`make db-upgrade`).

<details><summary>Send commands from your host to a long-running container</summary>
<p>
If you want to re-use a docker application for various Python and development
 <code>make</code> commands (e.g. linting and testing), you should set
 <code>RUN_CMD_OPT</code> to <code>DOCKER_EXEC</code>.

```sh
$ export RUN_CMD_OPT=DOCKER_EXEC
$ make test
```

</p>
</details>

<details><summary>Log into a docker container to run commands</summary>
<p>If you intend to start a Docker environment and log into it like a remote server,
 you can leave <code>RUN_CMD_OPT</code> alone and use <code>make login</code> instead.

```sh
$ make login
> make test
```

</p>
</details>

<details><summary>Start a new docker container for every command</summary>
<p>If you plan to run commands through temporary, single-use Docker containers, you
 should set your <code>RUN_CMD_OPT</code> to <code>DOCKER_RUN</code>:

```sh
$ export RUN_CMD_OPT=DOCKER_RUN
$ make test
```

Note this is the default setting.

</p>
</details>

<details><summary>Mix and Match</summary>
 <p>If you plan to mix and match things, you'll have to juggle <code>RUN_CMD_OPT</code> yourself.

For example:

- running static lints outside of Docker with native developer setup: <code>RUN_CMD_OPT=NATIVE make lint</code>
- running tests inside of Docker after a <code>make start</code>: <code>RUN_CMD_OPT=DOCKER_EXEC make test</code>

</p>
</details>

#### Native Developer Setup

To setup a development environment outside of Docker, you'll need to install a
few things.

1. Install at least Python 3.8.
   [pyenv](https://github.com/pyenv/pyenv#installation) is one popular option
   for installing Python, or [asdf](https://asdf-vm.com/).
2. After installing and activating the right version of Python, install
   [poetry](https://python-poetry.org/docs/#installation).
3. Install [Node.js](https://nodejs.org/en/) (v10 or greater).
   [nvm](https://github.com/nvm-sh/nvm) is one popular option. Similar to
   Python, [asdf](https://asdf-vm.com/) is another option.
4. Set `RUN_CMD_OPT` to `NATIVE` in your development environment.
5. Run `make deps` to install Python dependencies and development tooling.

You should now be able to run developer tooling natively, like linting.

To run the application you'll need some environment variables set. You can
largely copy-paste the env vars in `docker-compose.yml` to your native
environment. `DB_HOST` should be changed to `localhost`. You can then start up
just the PostgreSQL database via Docker with `make start-db` and then the API
server with `make run-native`.

### Development Workflow

All mandatory checks run as part of the Github CI pull request process. See the
`api-*.yml` files in [/.github/workflows](/.github/workflows) to see what
gets run.

You can run these checks on your local machine before the PR stage (such as
before each commit or before pushing to Github):

- `make format` to fix any formatting issues
- `make check` to run checks (e.g. linting, testing)
  - See the other `check-static` and `lint-*` make targets, as well as the Tests
    section below to run more targeted versions of these checks

## How it works

### Key Technologies

The API is written in Python, utilizing Connexion as the web application
framework (with Flask serving as the backend for Connexion). The API is
described in the OpenAPI Specification format in the file
[openapi.yaml](/api/openapi.yaml).

SQLAlchemy is the ORM, with migrations driven by Alembic. pydantic is used in
many spots for parsing data (and often serializing it to json or plain
dictionaries). Where pydantic is not used, plain Python dataclasses are
generally preferred.

- [OpenAPI Specification][oas-docs]
- [Connexion][connexion-home] ([source code][connexion-src])
- [SQLAlchemy][sqlalchemy-home] ([source code][sqlalchemy-src])
- [Alembic][alembic-home] ([source code](alembic-src))
- [pydantic][pydantic-home] ([source code][pydantic-src])

[oas-docs]: http://spec.openapis.org/oas/v3.0.3
[oas-swagger-docs]: https://swagger.io/docs/specification/about/

[connexion-home]: https://connexion.readthedocs.io/en/latest/
[connexion-src]: https://github.com/zalando/connexion

[pydantic-home]:https://pydantic-docs.helpmanual.io/
[pydantic-src]: https://github.com/samuelcolvin/pydantic/

[sqlalchemy-home]: https://www.sqlalchemy.org/
[sqlalchemy-src]: https://github.com/sqlalchemy/sqlalchemy

[alembic-home]: https://alembic.sqlalchemy.org/en/latest/
[alembic-src]: https://github.com/sqlalchemy/alembic

### Request operations

- OpenAPI spec (`openapi.yaml`) defines API interface: routes, requests, responses, etc.
- Connexion connects routes to handlers via `operationId` property on a route
  - Connexion will run OAS validations before reaching handler
  - Connexion will run authentication code and set user in the request context
  - The handlers generally live in the top level files at
    [massgov/pfml/api](/api/massgov/pfml/api/), with the `operationId` pointing
    to the specific module and function
- Handlers check if user in request context is authorized to perform the action
  the request represents
- Handlers use pydantic models to parse request bodies and construct response data
- Connexion will run OAS validations on response format from handler

### Authentication

Authentication methods are defined in the `securitySchemes` block in
`openapi.yaml`. A particular security scheme is enabled for a route via a
`security` block on that route. Note the `jwt` scheme is enabled by default for
every route via the global `security` block at the top of `openapi.yaml`.

Connexion runs the authentication before passing the request to the route
handler. In the `jwt` security scheme, the `x-bearerInfoFunc` points to the
function that is run to do the authentication.

### Authorization

Authorization is handled via the
[bouncer](https://github.com/bouncer-app/bouncer) and
[flask-bouncer](https://github.com/bouncer-app/flask-bouncer) libraries.

The rules are defined in
[massgov/pfml/api/authorization/rules.py](/api/massgov/pfml/api/authorization/rules.py),
and request handlers use the `ensure` and `can` functions provided by
flask-bouncer (re-exported in
[massgov/pfml/api/authorization/flask.py](/api/massgov/pfml/api/authorization/flask.py)
for use in the application, as we may eventually want to provide slightly
modified versions of the functions provided by flask-bouncer directly) to check
if the user in the current request context is authorized to perform the given
action on the given subject.

## Running the Application (Docker)

#### Initializing dependencies

The application requires a running database with some minimum level of
migrations already run as well as database users created and various other
things.

`make init` will perform the prep tasks necessary to get the application off the
ground.

#### Common commands

```sh
make start    # Start the API
make logs     # View API logs
make login    # Login to the container, where you can run development tools
make login-db # Start a psql prompt in the container, where you can run SQL queries. requires make login.
make build    # Rebuild container and pick up new environment variables
make stop     # Stop all running containers
```

#### Managing the container environment

Under most circumstances, a local copy of the API will run with `use_reloader=True`,
a flag given to Connexion that automatically restarts the the API's Python process if any modules have changed.
Most of the time, the `use_reloader` flag should take care of things for you, but there are
a few scenarios where you'll need to make a manual intervention in order to properly manage your container's state.

If you're doing work on a local environment, please be aware that any changes to *environment variables* or *config files*
will require a _rebuild_ of the API's Docker image. Do this with `make stop` followed by `make build.`

If you're only changing application code, you won't need to rebuild anything,
_unless_ you're changing code that runs before the `connexion_app.run` command in
[__main__.py](https://github.com/EOLWD/pfml/blob/main/api/massgov/pfml/api/__main__.py#L57).
In this case only, you'll need to restart the Docker containers with `make stop` followed by `make start`.

These scenarios are most relevant to developers who habitually work in `DOCKER_EXEC` mode,
with long-lived application and DB containers.

#### Running migrations

When you're first setting up your environment, ensure that migrations are run
against your db so it has all the required tables. `make init` does this, but if
needing to work with the migrations directly, some common commands:

```sh
make db-upgrade       # Apply pending migrations to db
make db-downgrade     # Rollback last migration to db
make db-downgrade-all # Rollback all migrations
```

#### Creating new migrations

If you've changed a python object model, auto-generate a migration file for the database and run it:

```sh
$ make db-migrate-create MIGRATE_MSG="<brief description of change>"
$ make db-upgrade
```

<details>
    <summary>Example: Adding a new column to an existing table:</summary>

1. Manually update the database models with the changes (`massgov/pfml/db/models/employees.py` in this example)
```python
class Address(Base):
    ...
    created_at = Column(TIMESTAMP(timezone=True)) # Newly added line
```

2. Automatically generate a migration file with `make db-migrate-create MIGRATE_MSG="Add created_at timestamp to address table"`
```python
...
def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("address", sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("address", "created_at")
    # ### end Alembic commands ###
```

3. Manually adjust the migration file as needed. Some changes will not fully auto-generate (like foreign keys), so make sure that all desired changes are included.
</details>

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
you'll need to fix the migration branches/heads before merging to `main`.

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

#### Create application DB users

The migrations set up the DB roles and permissions. After the migrations have
been run, actual DB users need to be connected for the application to use.

```sh
make db-create-users
```

## Try it out

Once your application is running, a UI is available at:

- [http://localhost:1550/v1/docs/](http://localhost:1550/v1/docs/)

The spec is available at:

- [http://localhost:1550/v1/openapi.json](http://localhost:1550/v1/openapi.json) (JSON) or
- [http://localhost:1550/v1/openapi.yaml](http://localhost:1550/v1/openapi.yaml) (YAML)

### Getting local authentication credentials

#### User authentication

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

#### Machine-to-machine authentication

Some endpoints require a `client_id` and `client_secret`. For these, you will need to configure your environment to point to a real Cognito resource:

1. Copy credentials in the ["Testing" section of this Confluence page](https://lwd.atlassian.net/l/c/CRjiWu8L), you'll need these for later steps.
1. Update the `COGNITO_USER_POOL_KEYS_URL` setting in `docker-compose.yml` to point to one of our environments. There should be one already in the file that you can uncomment.
1. Update `tokenUrl` in the `openapi.yaml` to the Cognito address (for stage: `https://massgov-pfml-stage.auth.us-east-1.amazoncognito.com/oauth2/token`)
1. Create a user: `make create-user args=fineos` 
1. In a tool like Postico, edit the DB record for the user, and change its `active_directory_id` to the `client_id`
1. Re-build and restart the Docker container


### Seed your database

Some interactions require valid data and associations to exist within the database, such as a valid `Employer` and `Employee`. 

To create a leave admin user account with claims, run:

```
make create-leave-admin-and-claims
```

The script above will output information you can use to then generate the JWT, which you can use in Swagger to perform API requests as the generated leave admin.

Another way to seed your database is to run a mock DOR import:

Generate a fake DOR file:

```
make dor-generate
```

Run the DOR import locally:

```
make dor-import
```

After the scripts above have ran, you can grab values from your database tables using a tool like [Postico](https://eggerapps.at/postico/).

## Tests

For writing tests see [/docs/api/writing-tests.md](/docs/api/writing-tests.md).

There are various `test*` make targets set up for convenience.

To run the entire test suite:

```sh
make test
```

Ultimately the targets just wrap the test runner
[pytest](https://docs.pytest.org) with minor tweaks and wrapping it in helper
tools. To pass arguments to `pytest` through `make test` you can set the `args`
variable.  For example, to run only the tests in `test_user.py`:

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

For a more complete description of the many ways you can select tests to run and
different flags, [refer to the pytest
docs](https://docs.pytest.org/en/latest/usage.html) (and/or `pytest --help`).

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
make test-watch-changed
```

To run tests decorated with `@pytest.mark.dev_focus` whenever a file is saved:

```sh
make test-watch-focus
```

`test-watch-focus` is a wrapper around the more flexible `test-watch` Makefile target
that we can use to re-run specific tests whenever a file changes, for instance.

```sh
make test-watch args=tests/api/test_users.py::test_users_get
```

Arguments for `test-watch` are the same as args for `make test` as discussed in the section above.

To run only unit tests:

``` sh
make test-unit
```

## Managing dependencies

Python dependencies are managed through poetry. See [its
docs](https://python-poetry.org/docs/) for adding/removing/running Python things
(or see `poetry --help`).

Cheatsheet:

| Action                              | Command                                    |
| ----------------------------------- | ------------------------------------------ |
| Add a dependency                    | `poetry add <package name> [--dev]`        |
| Update a dependency                 | `poetry update <package name>`             |
| Remove a dependency                 | `poetry remove <package name>`             |
| See installed package info          | `poetry show [package name]`               |
| Run a command in Python environment | `poetry run <cmd>`                         |
| See all package info                | `poetry show [--outdated] [--latest]`      |
| Upgrade package to latest version   | `poetry add <package name>@latest [--dev]` |

### poetry.lock conflicts

Poetry maintains a `metadata.content-hash` value in its lock file
(`poetry.lock`) which is the hash of the sorted contents of the `pyproject.toml`
(helps keep track of if the lock file is out of date with declared dependencies
and such).

This can be a cause of merge conflicts.

To resolve:

- Pick either side of the conflict (i.e., edit the `content-hash` line to either hash)
- Then run `make update-poetry-lock-hash` to update the hash to the correct value

## Environment Configuration

Environment variables for the local app are in the `docker-compose.yml` file.

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

Changes here will be picked up next time `make start` is run.

## How deploys work

There are two ways code gets run in hosted environments, as tasks on [AWS
Elastic Container Service (ECS) clusters][ecs-docs] (backed by [AWS
Fargate][fargate-docs]) and as [AWS Lambdas][lambda-docs].

[ecs-docs]: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/Welcome.html
[fargate-docs]: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/AWS_Fargate.html
[lambda-docs]: https://docs.aws.amazon.com/lambda/latest/dg/welcome.html

For actually performing deploys, see
[/docs/api/deployment.md](/docs/api/deployment.md).

### ECS

ECS tasks all share the same container as built by the `app` stage of the
`Dockerfile`. This stage builds the project Python package (basically zip up
[massgov/](/api/massgov)) and installs it into the container environment.

This also has the effect of making the package entrypoints as listed in the
`[tool.poetry.scripts]` section of [pyproject.toml](/api/pyproject.toml)
available on `PATH`, so ECS tasks besides the Paid Leave API server tend to set
one of these as their Docker command.

The Paid Leave API server ECS task is declared in
[/infra/api/template/service.tf](/infra/api/template/service.tf) as well as its
ECS service, which is a wrapper for ECS tasks to ensure a specified number of
the tasks are running, provides mechanisms for autoscaling, and various other
"service" features.

Other ECS tasks are in
[/infra/ecs-tasks/template/tasks.tf](/infra/ecs-tasks/template/tasks.tf). These
are not a part of an ECS service, the tasks are launched/started on demand
(either by an automated process like a scheduled AWS EventBridge event, Step
Function, or manually through the [/bin/run-ecs-task](/bin/run-ecs-task/) tool).

### Lambda

Lambdas are a little different. Their main source code lives somewhere in
[massgov/](/api/massgov), with their build infrastructure in
[lambdas/](/api/lambdas) which is mostly boilerplate to import the correct
module from [massgov/](/api/massgov) and build it as appropriate for the Lambda
runtime.

The Lambda building happens via the AWS Serverless Application Model (SAM) CLI
tool, which takes the project Python package and builds its dependencies inside
a Docker container matching the Lambda runtime environment (for cases where a
dependency needs a compiled component). This generates a ZIP of the Lambda,
which can then be uploaded to S3.

The Lambda configuration and deploys are done in Terraform, at
[/infra/api/template/lambda.tf](/infra/api/template/lambda.tf).

## Monitoring and Alerting

The API is monitored with New Relic's Python agent.
Config variables and env-specific settings for New Relic live inside `newrelic.ini` and `container_definitions.json`.
See [environment-variables.md](/docs/api/environment-variables.md) for more about how env vars are pulled in at runtime.

## Releases

More details about how to handle releases are available in the [release
runbook](https://lwd.atlassian.net/wiki/spaces/DD/pages/818184193/API+and+Portal+Runbook).

As a part of the release process it is useful to include some technical notes on
what the release includes. There is a make target to help automate some of this:

```sh
make release-notes
```

This will generate a list of the commits impacting an API release. For the
commits that follow the project convention for commit messages, the Jira ticket
will be linked. Everyone does not follow the convention nor will every commit
have a Jira ticket associated.

But this will provide a starting point. By default it will generate the list of
commits that are different between what is deployed to stage (indicated by the
`deploy/api/stage` branch) and what is on `main`. You can change the range of
commits it considers by passing in `refs`, for example only looking for changes
between release candidates:

```sh
make release-notes refs="api/v1.3.0-rc1..api/v1.3.0-rc2"
```

The work will generally fall into one of a number of categories, with changes to:
- ECS tasks for background jobs
- The API service itself
- CI tweaks

It's useful to group the release notes broadly by these buckets to clarify what
this particular release will impact.

It's also usually useful to group the tickets by team, which piping to `sort`
can help facilitate:

```sh
make release-notes | sort
```

Ultimately culminating in something like the notes for
[api/v1.3.0](https://github.com/EOLWD/pfml/releases/tag/api%2Fv1.3.0).

## Figuring out what's released where

There are a couple other make targets that could be useful. Note these all work
off of your local git repo, so can only be as accurate as your local checkout
is. You will generally want to run `git fetch origin` before these if you want
the most up-to-date info.

`where-ticket` will search the release branches for references to the provided
ticket number:

```sh
$ make where-ticket ticket=API-1000
## origin/main ##
e7fb31752 API-1000: Do not add "MA PFML - Limit" plan to FINEOS service agreements (#2272)

## origin/deploy/api/stage ##
e7fb31752 API-1000: Do not add "MA PFML - Limit" plan to FINEOS service agreements (#2272)

## origin/deploy/api/prod ##
e7fb31752 API-1000: Do not add "MA PFML - Limit" plan to FINEOS service agreements (#2272)

## origin/deploy/api/performance ##
e7fb31752 API-1000: Do not add "MA PFML - Limit" plan to FINEOS service agreements (#2272)

## origin/deploy/api/training ##

```

So in this example, API-1000 has been deployed to every environment but `training`.

`whats-released` lists some info about the latest commits on the release branches:

```sh
$ make whats-released
## origin/main ##
 * Closest tag: api/v1.3.0-rc2-48-g4465cfb72
 * Latest commit: 4465cfb72 (origin/main, main) END-338: Convert employer response and remove notification checking (#2386)

## origin/deploy/api/stage ##
 * Closest tag: api/v1.3.0
 * Latest commit: 6e86eab29 (tag: api/v1.3.0-rc3, tag: api/v1.3.0, origin/deploy/api/stage, origin/deploy/api/prod) EMPLOYER-685 Add logging reqs to LA FINEOS registration script (#2349)

## origin/deploy/api/prod ##
 * Closest tag: api/v1.3.0
 * Latest commit: 6e86eab29 (tag: api/v1.3.0-rc3, tag: api/v1.3.0, origin/deploy/api/stage, origin/deploy/api/prod) EMPLOYER-685 Add logging reqs to LA FINEOS registration script (#2349)

## origin/deploy/api/performance ##
 * Closest tag: api/v1.3.0-rc2
 * Latest commit: 13ba0f2c3 (tag: api/v1.3.0-rc2, origin/deploy/api/performance) remove ecr scan github action (#2333)

## origin/deploy/api/training ##
 * Closest tag: api/v1.1.0-rc1-48-ga6fb1f6bc
 * Latest commit: a6fb1f6bc (origin/deploy/api/training) API-999 Prod-Check Not Working as Expected (#2322)
```

So here can see `api/v1.3.0` is on both `stage` and `prod`, `performance` is on
`api/v1.3.0-rc2`, and something a little ahead of `api/v1.1.0-rc1` is on
`training`.

## Directory Structure

```
.
├── lambdas                     Build/packaging configurations for AWS Lambdas
├── massgov                     Python package directory
│   └── pfml
│       └── api                 Application code
│       └── db
│           └── migrations      Migrations config
│               └── versions    Migrations themselves
├── tests
│   └── api             Application tests
├── Dockerfile          Multi-stage Docker build file for project
├── docker-compose.yml  Config file for docker-compose tool, used for local development
├── openapi.yaml        API specification
├── pyproject.toml      Python project configuration file
├── newrelic.ini        New Relic configuration file
└── setup.cfg           Python config for tools that don't support pyproject.toml yet
```
