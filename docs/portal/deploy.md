# Deploy

## Deploy to stage or your own environment

Deployment is handled by Github Actions and is triggered by pushing changes to the deployment environment's branch.
(for more details, see [Creating Environment](./creating-environments))

In your local environment, run

```sh
git checkout <<branch_name>>
git reset --hard master
git push origin <<branch_name>>
```

For example, to deploy to stage, run

```sh
git checkout deploy/stage
git reset --hard master
git push origin deploy/stage
```
