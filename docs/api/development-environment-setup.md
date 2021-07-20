# Development Environment Setup

- [Setup Methods](#setup-methods)
  - [(Preferred) Docker + GNU Make](#preferred-docker--gnu-make)
  - [Native Developer Setup](#native-developer-setup)
- [Environment Configuration](#environment-configuration)
- [Development Workflow](#development-workflow)
- [Makefile utilities](#makefile-utilities)
- [Managing Python dependencies](#managing-python-dependencies)
  - [poetry.lock conflicts](#poetrylock-conflicts)

## Setup Methods

You can set up your development environment in one of the following ways:

1. (Preferred) Docker + GNU Make
2. Native developer setup: Install dependencies directly on your OS

### (Preferred) Docker + GNU Make

Docker is heavily recommended for a local development environment. It sets up Python, Poetry and installs development
dependencies automatically, and can create a full environment including the API application and a backing database.

Follow instructions here to [install Docker](https://docs.docker.com/get-docker/) for your OS.

In a docker-centric environment, we support a couple different developer workflows:

| Start command from: | Container Lifetime | RUN_CMD_OPT |
| ------------------- | ------------------ | ----------- |
| your host 🙋‍♀️         | Long-running       | DOCKER_EXEC |
| inside docker 🐳     | Long-running       | N/A         |
| your host 🙋‍♀️         | Single-use         | DOCKER_RUN  |
| Mixed               | Mixed              | Mixed       |

The default is `DOCKER_RUN` and should always just work™. But this spins up a new container for every command, which can
be slow. If you are working on the API a lot, you may want to consider one of the alternative setups below and/or
the [Native Developer Setup](#native-developer-setup).

**Note: Some tasks, including initial setup, will usually need to be run with `DOCKER_RUN`** regardless of the workflow
used otherwise. Examples include generating an initial local JWKS
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

### Native Developer Setup

To setup a development environment outside of Docker, you'll need to install a few things.

1. Install at least Python 3.8.
   [pyenv](https://github.com/pyenv/pyenv#installation) is one popular option for installing Python,
   or [asdf](https://asdf-vm.com/).
2. After installing and activating the right version of Python, install
   [poetry](https://python-poetry.org/docs/#installation).
3. Install [Node.js](https://nodejs.org/en/) (v10 or greater).
   [nvm](https://github.com/nvm-sh/nvm) is one popular option. Similar to Python, [asdf](https://asdf-vm.com/) is
   another option.
4. Set `RUN_CMD_OPT` to `NATIVE` in your development environment.
5. Run `make deps` to install Python dependencies and development tooling.

You should now be able to run developer tooling natively, like linting.

To run the application you'll need some environment variables set. You can largely copy-paste the env vars
in `docker-compose.yml` to your native environment. `DB_HOST` should be changed to `localhost`. You can then start up
just the PostgreSQL database via Docker with `make start-db` and then the API server with `make run-native`.

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

## Development Workflow

All mandatory checks run as part of the Github CI pull request process. See the
`api-*.yml` files in [/.github/workflows](/.github/workflows) to see what gets run.

You can run these checks on your local machine before the PR stage (such as before each commit or before pushing to
Github):

- `make format` to fix any formatting issues
- `make check` to run checks (e.g. linting, testing)
    - See the other `check-static` and `lint-*` make targets, as well as the Tests section below to run more targeted
      versions of these checks

## Makefile utilities

Many of the utilities and scripts to developing and managing the application have been standardized into
a ([GNU make/Makefile](https://www.gnu.org/software/make/manual/make.html). This makes the command format more
consistent, and centralizes where the tools are managed.

> If you need an automated script to perform a task, check the Makefile! It may already exist!

Each component of the system may have its own set of `make` "targets" with their own in-depth documentation.

TODO: Update w/ link to more detailed documentation ([API-1477](https://lwd.atlassian.net/browse/API-1477))

## Managing Python dependencies

Python dependencies are managed through `poetry`. See [its docs](https://python-poetry.org/docs/) for
adding/removing/running Python things
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
(helps keep track of if the lock file is out of date with declared dependencies and such).

This can be a cause of merge conflicts.

To resolve:

- Pick either side of the conflict (i.e., edit the `content-hash` line to either hash)
- Then run `make update-poetry-lock-hash` to update the hash to the correct value
