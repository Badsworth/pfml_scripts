# Massachusetts Paid Family & Medical Leave

This is the top level of the monorepo for the Mass PFML project, including web portal and API. **View the `README` in each child directory for information specific to each system component.**

**You may also be interested in:**

- [Documentation](https://eolwd.github.io/pfml), specifically [CONTRIBUTING](https://eolwd.github.io/pfml/contributing)
- [Environments](https://lwd.atlassian.net/wiki/spaces/DD/pages/246612440/Environments)

## Documentation

Documentation specifically relevant to people working on the codebase is stored as Markdown pages in [/docs](./docs). These pages are rendered by [mkdocs](https://www.mkdocs.org/) and automatically deployed by GitHub Actions whenever a new change is merged into the main branch. The deployed docs live in the `gh-pages` branch.

You can serve the website locally by running `npm run docs` and visiting `http://localhost:8000`. This allows you to verify the rendering of your built docs before merging.

To make configuration updates to mkdocs or the deployment workflow, see [mkdocs.yml](./mkdocs.yml) and [docs-deploy.yml](./.github/workflows/docs-deploy.yml).

## Developer Setup

To ensure consistent Node/NPM versions are used, install [Volta](https://volta.sh/). Volta is similar to NVM, but is faster and requires almost no setup. Once Volta is installed, it should automatically use the project-pinned versions of `node` and `npm` with no additional work, including installing the correct versions if you don't have them already.

```shell
curl https://get.volta.sh | bash
exec $SHELL # ... or otherwise restart your shell.
```

When initially setting up the project, install packages from the repo root to enable git hooks.

```
npm install
```

To ensure Terraform (infra) files are linted, install Terraform. The best way to manage Terraform versions is with [Terraform Version Manager](https://github.com/tfutils/tfenv).

```
$ brew install tfenv
$ tfenv install 0.14.7
```

### Using pre-commit hooks

In order for our pre-commit hooks to work properly, you'll need to have a supported version of Node installed and have run `npm install` in the root directory. Once you've completed those steps, pre-commit hooks should work with any of the API's [Development Environment Setup](docs/api/development-environment-setup.md) options. If you have not set `RUN_CMD_OPT` the pre-commit hooks will default to running in docker.

We're using husky and lint-staged to manage our pre-commit hooks so that they only run on relevant file changes. Here are the details on which changes will trigger which checks:

| File(s) changed                               | Command                                | What's being checked                                    |
|-----------------------------------------------|---------------------------------------------|---------------------------------------------------------|
| Files in the `portal/` directory              | `npm run format --prefix=portal -- --write` | Formatting (prettier)                                   |
| Any `.tf` or `.tfvars` files                  | `npm run lint:tf`                           | Formatting (terraform fmt)
| `.py` files in the `api/` directory           | `make pre-commit`                           | Formatting (isort & black) and linting (flake8 & mypy)  |
| Files in the `api/massgov/pfml/db/` directory | `make db-check-model-parity`                | Ensure application models are in sync with the database |
| `api/openapi.yaml`                            | `make lint-spectral`                        | OpenAPI spec linting                                    |

While using the pre-commit hooks is highly encouraged, if you ever need to force a commit to go through without passing the pre-commit hooks, you can commit with the `--no-verify` flag. 

### Additional commands

#### `npm run lint:tf`

Formats the Terraform files.

## Directory Structure

```
└── .github                 🗂 GitHub actions and templates
└── admin                   🔑 Admin portal
└── api                     🔀 Integration API
└── bin                     🤖 Developer scripts
└── docs                    🔖 Developer documentation
└── e2e                     🏁 End-to-end & business simulation tests
└── infra                   🌲 Infrastructure config
└── portal                  🚪 Claimant and Employer portal
```
