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

When initially setting up the project, install packages from the repo root to enable git hooks.

```
npm install
```

To ensure Terraform (infra) files are linted, install Terraform. The best way to manage Terraform versions is with [Terraform Version Manager](https://github.com/tfutils/tfenv).

```
$ brew install tfenv
$ tfenv install 0.14.7
```

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
