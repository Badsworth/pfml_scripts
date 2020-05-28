# Massachusetts Paid Family & Medical Leave

This is the top level of the monorepo for the Mass PFML project, including web portal and API. View the `README` in each child directory for information specific to each system component.

**You may also be interested in:**

- [`docs/`](./docs/)
- [Environments](https://lwd.atlassian.net/wiki/spaces/DD/pages/246612440/Environments)

## Installation

When initially setting up the project, install packages from the repo root to enable git hooks and linting.

```
npm install
```

To ensure terraform (infra) files are linted, install terraform. The best way to manage terraform versions is with [Terraform Version Manager](https://github.com/tfutils/tfenv).

```
$ brew install tfenv
$ tfenv install 0.12.24
```

## Portal

### Prerequisites

Node v10 (or greater)

### Run Instructions

Run the web portal locally from the project root directory with the following commands:

```
npm install --prefix portal
npm run dev --prefix portal
```

### Additional commands

#### `npm run lint`

Run all linters. Fixes any [auto-fixable ESLint errors](https://eslint.org/docs/user-guide/command-line-interface#fixing-problems) and formats the Terraform files.

[Integrate ESLint into your IDE or a git hook](https://eslint.org/docs/user-guide/integrations) if you'd like to catch linting errors before it reaches the CI.

#### `npm run lint:ci`

Runs all linters and fails on errors. Does not attempt to auto-fix ESLint errors.

#### `npm run lint:js`

Lint JS files using [ESLint](https://eslint.org/).

#### `npm run prettier`

Automatically format files using [Prettier](https://prettier.io/).

## API

TBD

## Directory Structure

```
└── .github                 🗂 GitHub actions and templates
└── api                     🔀 Integration API
└── bin                     🤖 Developer scripts
└── docs                    🔖 Developer documentation
└── infra                   🌲 Infrastructure config
└── portal                  🚪 Claimant portal web app
```
