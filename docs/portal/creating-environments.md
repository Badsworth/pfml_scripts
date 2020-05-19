# Setting up a new environment

This docs covers the steps you need to take to configure the Portal web app to support a new environment.

Before reading this, make sure you've already ran through the [steps to setup the infrastructure for a new environment](../creating-environments.md).

## Add environment variables

1. Create a new config file for the environment in [`portal/config`](../../portal/config), copying the properties from another environment.
1. Update the variables for the environment. Primarily, you'll want to update the environment name and the Cognito IDs, which should have been output after you ran `terraform apply`
1. Add an entry for the new environment to [`portal/config/index.js`](../../portal/config/index.js), copying the properties from another environment.

## Add a build script

Each environment should have its own build script in `portal/package.json` so that the site can be built using the correct environment variables. Refer to other build scripts, like `build:test` for an example.

## Update GitHub Actions

Each environment will have its own GitHub branch that will deploy when changes are pushed. Add your branch and environment configs to [`portal-deploy.yml`](../../.github/workflows/portal-deploy.yml) _and_ [`portal-infra-deploy.yml`](../../.github/workflows/portal-infra-deploy.yml) by adding a branch to the workflow trigger:

```yml
on:
  push:
    branches:
      - master
      - deploy/<<environment_name>>
```

and environment variables:

```yml
env:
  # ...
  # map branch name to environment name
  refs/heads/master: test
  refs/heads/deploy/<<environment_name>>: <<environment_name>>
```

Also update the [deploy](./deploy.md) doc with details about deploying to the new environment.
