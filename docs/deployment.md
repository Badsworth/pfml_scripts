# Deployment

Deployments to all API and Portal environments are managed through GitHub Actions.

- The `main` branch is automatically deployed to `test` as pull requests are merged into it.

- Deployments to other environmments are triggered manually.

Changes to the following components take effect immediately in all environments once they go into `main`:

- Alerts and Pagerduty configuration in [infra/monitoring](../infra/monitoring)
- Feature flags managed in the [feature_flags](../feature_flags) folder
- Github action workflows, as defined in [.github/workflows](../.github/workflows).

---

### Deploying to an API or Portal environment

1. Visit the API or Portal Github Actions homepage:

    - [API Deploy](https://github.com/EOLWD/pfml/actions?query=workflow%3A%22API+CI+Deploy%22)
    - [Portal Deploy](https://github.com/EOLWD/pfml/actions?query=workflow%3A%22Portal+Deploy%22)

1. Click the "Run workflow" button, and fill in the inputs:

    - Provide the `deployment_env` from the list of environments.
    - Provide a git branch or tag to deploy. This can be:
        - the name of a git tag, e.g. `api/v1.7.0-rc1`, or 
        - the name of a git branch, like `release/api/v1.7.0` or `kev/my-feature-branch`.

1. Click the green "Run workflow" button.

### Test Environment Coordination

If you are testing a feature branch on the test environment, please go through the following additional steps:

#### During Testing
- [ ] Communicate to the Deployments channel in Teams: "⚠️ I'll be using the API/Portal test environment soon, please let me know if you have any concerns."
- [ ] After running the workflow, click the "Disable Workflow" button to prevent auto-deploys from overriding your deployment.

#### After Testing
- [ ] Click the "Enable Workflow" button.
- [ ] Re-deploy `main` to test.
- [ ] Notify the Teams channel.

### Branch-to-environment mapping

At a quick glance, you can view the commit history for any environment based on the branch.

| Name of API deploy branch | Name of Portal deploy branch | Corresponding env |
| ------------------------- | ---------------------------- | ----------------- |
| main                      | main                         | test              |
| deploy/api/stage          | deploy/portal/stage          | stage             |
| deploy/api/prod           | deploy/portal/prod           | prod              |
| deploy/api/performance    | deploy/portal/performance    | performance       |
| deploy/api/training       | deploy/portal/training       | training          |
| deploy/api/uat            | deploy/portal/uat            | uat               |
