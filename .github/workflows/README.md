# GitHub Workflows

These workflows provide automation for the Mass PFML repo. The workflows fall into several main categories: Continuous Integration (CI), and
Continuous Deployment (CD).

All workflows are triggered by particular GitHub events, specified in the `on` clause. This clause can include branch and/or path sub-specifications.

For more information on GitHub Actions, see [the docs](https://help.github.com/en/actions).

## Naming

If you are creating a new workflow, please follow this convention:

```
<component>-<workflow-type>-<description>
```

Components should match one of the top-level directories. The workflow type should match one of the following:

- **deploy**: Workflows that deploy changes to environments
- **tests**: Workflows that run tests (e.g. linting, unit tests) during PRs or deployments
- **scheduled-alerts**: Workflows that run on a schedule and may trigger alerts
- **scheduled**: Workflows that run on a schedule
- **on-demand**: Workflows that are only run manually, either through workflow_dispatch or through PR comments.

### Meta-automation

Some workflows take action on other GitHub workflows, e.g. listening to certain repository updates and triggering certain PR checks to run again.

These have the following naming convention: `<component>-<workflow-type>-monitor-*.yml`.
