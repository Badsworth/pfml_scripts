# Deploy

Deploys to test, stage, and prod environments are done with Github Actions workflows. Pushes to the following branches will trigger deploys to the associated environments:

| Branch                | Environment|
|-----------------------|-----------|
| `master`              | test |
| `deploy/portal/stage` | stage |
| `deploy/portal/prod`  | prod |

The `master` branch is automatically deployed as pull requests are merged into it. The remaining branches are generally pushed to as part of a release cycle, but may also be triggered manually.

## Triggering a manual deploy

All you have to do to trigger a deploy to a specific environment is to push your desired branch to the deploy branch for that environment from your computer. For example:

```sh
git checkout <<deploy_branch_name>>
git reset --hard <<desired_branch>>
git push origin <<deploy_branch_name>>
```

To deploy the `master` branch to the stage environment, run

```sh
git checkout deploy/portal/stage
git reset --hard master
git push origin deploy/portal/stage
```

**Caution:** this means that an accidental push to the `deploy/portal/prod` branch will trigger a deploy to production.
