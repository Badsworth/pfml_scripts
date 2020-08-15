# Deploy

Deploys to test, stage, and prod environments are done with Github Actions workflows.
Pushes to the following branches will trigger deploys to the associated environments:

| Branch                | Environment |
| --------------------- | ----------- |
| `master`              | test        |
| `deploy/api/stage`    | stage       |
| `deploy/api/prod`     | prod        |

The `master` branch is automatically deployed to `test` as pull requests are merged into it.
The remaining branches are generally pushed to as part of a release cycle, but they may also be triggered manually.

---

## Triggering a manual deploy

There are two ways to trigger a manual deploy: from the command line, and from the GitHub UI.

---

### Deploying from the GitHub UI

!!! note

    This method can only be used to deploy a branch to `test`.
    Use the git-based method if you need to deploy to any other environment.

Manual deployment of any branch to `test` is possible through the GitHub user interface.
This is useful to, for example, test the functionality of a feature branch in a realistic environment
before that branch has been merged.

All you have to do to deploy the API using this method is: 

- Visit [the API CI Deploy action homepage](https://github.com/EOLWD/pfml/actions?query=workflow%3A%22API+CI+Deploy%22) on GitHub.
- Click the "Run workflow" button, and select the branch you wish to use. `master` is the default, but any branch can be selected.
- Click the green "Run workflow" button. The `HEAD` of your chosen branch will be deployed to `test`, as in the git-based workflow.

---

### Deploying from the command line

All you have to do to trigger a deploy to a specific environment is 
to push your desired branch to the deploy branch for that environment from your computer. For example:

```sh
git checkout <<deploy_branch_name>>
git reset --hard <<desired_branch>>
git push origin <<deploy_branch_name>>
```

!!! Caution
    
    Any push to the `deploy/api/prod` branch will trigger a deploy to production.

#### Deploying master to staging

To deploy the `master` branch to the stage environment, run

```sh
git checkout deploy/api/stage
git reset --hard master
git push origin deploy/api/stage
```

#### Deploying staging to prod

To deploy the code in the `staging` environment to the prod environment, run

```sh
git checkout deploy/api/prod
git reset --hard deploy/api/stage
git push origin deploy/api/prod
```
