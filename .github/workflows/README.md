# GitHub Workflows

These workflows provide automation for the Mass PFML repo. The workflows fall into several main categories: Continuous Integration (CI), and
Continuous Deployment (CD).

All workflows are triggered by particular GitHub events, specified in the `on` clause. This clause can include branch and/or path sub-specifications.

For more information on GitHub Actions, see [the docs](https://help.github.com/en/actions).

## Continuous Integration

To preserve the health of the main branch, tests and other checks (linting, etc.) are triggered by `pull_request` events.

Workflows with the name patterns `<component>-ci.yml` or `<component>-validate.yml` fall into this category.

## Continuous Deployment

These workflows automate the steps involved in cutting releases and rolling them out, triggered by `push` events.

These have the name pattern `<component>-deploy.yml`.

## Meta-automation

These workflows take action on other GitHub workflows.

These have the name pattern `<component>-monitor.yml`.

## Testing Github Action Workflows

See [Github Action Workflows](../../docs/infra/6-github-action-workflows.md).
