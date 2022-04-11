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

To setup a development environment outside of Docker, you'll need to install a few things. Note that these instructions are for running the _application_ natively, and the database will still run within Docker.

1. Install Python 3.9.
   [pyenv](https://github.com/pyenv/pyenv#installation) is one popular option for installing Python,
   or [asdf](https://asdf-vm.com/).
2. After installing and activating the right version of Python, install
   [poetry](https://python-poetry.org/docs/#installation).
3. Run `poetry config virtualenvs.in-project true` so that the project dependencies are installed inside the project at `pfml/api/.venv`.
4. Set `RUN_CMD_OPT` to `NATIVE` in your development environment.
5. If you are using an M1 mac, you will need to install postgres as well: `brew install postgresql` (The psycopg2-binary is built from source on M1 macs which requires the postgres executable to be present)
6. Run `make deps` to install Python dependencies and development tooling.

You should now be able to run developer tooling natively, like linting.

To run the application:

1. You'll need some environment variables set. You can largely copy-paste the env vars
   in `docker-compose.yml` to your native environment. `DB_HOST` should be changed to `localhost`.
1. Start the database within Docker: `make start-db`
1. Start the API server: `make run-native`

**Troubleshooting tips for native setup:**

If you run into `sqlalchemy.exc.OperationalError` errors when first trying to run natively, make sure you don't have postgres running locally on the same port as the
postgres in Docker.

If you installed and ran `postgresql` via Homebrew, you can stop it by running:

```
brew services stop postgresql
```

## IDE Configuration

If the IDE of your choice does not appear below, refer to the VS Code instructions for hints on what needs to get configured.

### VSCode

Make sure that you have completed the native development setup first.  These instructions also assume that root workspace is `pfml` and not `pfml/api`.

1. Set the python interpreter to the python binary installed in the virtual environment
2. Create `pfml/api/.env` file. **The variables here are sourced from docker-compose.yml.  The primary difference is that the DB_HOST=localhost.**
3. Update the workspace settings at to `pfml/.vscode/settings.json`.  Make sure to update the mypy.configFile to the correct path

```text
# pfml/api/.env
ENVIRONMENT=local
DB_HOST=localhost
DB_NAME=pfml
DB_ADMIN_USERNAME=pfml
DB_ADMIN_PASSWORD=secret123
DB_USERNAME=pfml_api
DB_PASSWORD=secret123
DB_NESSUS_PASSWORD=nessussecret123
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
COGNITO_USER_POOL_KEYS_URL=file://./jwks.json
COGNITO_USER_POOL_ID=us-east-1_HpL4XslLg
COGNITO_USER_POOL_CLIENT_ID=10rjcp71r8bnk4459c67bn18t8
DASHBOARD_PASSWORD=secret123
LOGGING_LEVEL=massgov.pfml.fineos.fineos_client=DEBUG,massgov.pfml.servicenow.client=DEBUG
ENABLE_EMPLOYEE_ENDPOINTS=1
FOLDER_PATH=dor_mock
FINEOS_FOLDER_PATH=fineos_mock
RMV_API_BEHAVIOR=fully_mocked
RMV_CHECK_MOCK_SUCCESS=1
ENABLE_MOCK_SERVICE_NOW_CLIENT=1
ENABLE_EMPLOYER_REIMBURSEMENT_PAYMENTS=1
PORTAL_BASE_URL=https://paidleave.mass.gov
ENABLE_APPLICATION_FRAUD_CHECK=0
ENABLE_DOCUMENT_MULTIPART_UPLOAD=0
AGENCY_REDUCTIONS_EMAIL_ADDRESS=EOL-DL-DFML-Agency-Reductions@mass.gov
DFML_PROJECT_MANAGER_EMAIL_ADDRESS=
DISABLE_SENDING_EMAILS=1
PFML_EMAIL_ADDRESS=PFML_DoNotReply@eol.mass.gov
BOUNCE_FORWARDING_EMAIL_ADDRESS=PFML_DoNotReply@eol.mass.gov
PDF_API_HOST=https://mass-pfml-pdf-api
ENABLE_GENERATE_1099_PDF=1
GENERATE_1099_MAX_FILES=1000
ENABLE_MERGE_1099_PDF=1
ENABLE_UPLOAD_1099_PDF=1
UPLOAD_MAX_FILES_TO_FINEOS=10
TEST_FILE_GENERATION_1099=0
IRS_1099_CORRECTION_IND=0
IRS_1099_TAX_YEAR=2021
MOVEIT_SFTP_URI=sftp://foo@mass-pfml-sftp:22
SFTP_URI=sftp://foo@mass-pfml-sftp:22
ENABLE_FULL_CHECK_SOLUTION=0
```

```json
{
  // pfml/.vscode/settings.json
  "python.testing.unittestEnabled": false,
  "python.testing.pytestEnabled": true,
  "python.linting.mypyEnabled": true,
  "python.linting.pycodestyleEnabled": false,
  "python.linting.enabled": true,
  "python.testing.pytestArgs": [
    "api/tests"
  ],
  "python.envFile": "${workspaceFolder}/api/.env",
  "python.formatting.provider": "black",
  "mypy.configFile": "/Users/{path to pfml project}/pfml/api/pyproject.toml",
  "python.linting.flake8Args": [
    "--config=${workspaceFolder}/api/setup.cfg"
  ],
  "python.linting.mypyArgs": [
    "--exclude=\"api/tests/"
  ],
  "python.analysis.extraPaths": ["${workspaceFolder}/api"], // Setting is only required if your workspace is the entire PFML repo
  "[python]": {
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    }
  },
}

```

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

Note that should you wish to try out a backend change against a locally running instance of the portal, this is available to you by starting the backend with `make logs-local`. See [development.md](/portal/development#Frontend<>BackendConfiguration) for details.

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
