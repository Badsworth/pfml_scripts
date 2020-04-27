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
  releases: prod
  refs/heads/master: test
  refs/heads/deploy/<<environment_name>>: <<environment_name>>
```

## Setup the SES sender email address

By default, new environments send authentication emails using Cognito. However, production or production-like environments should use SES so it doesn't run into limitations.

1. Ensure you have someone who can access the inbox of the email you'll be setting so they can verify it.
1. Update the environments `main.tf` file with the email address it should use for sending Cognito emails, and change `cognito_use_ses_email` to `true`
1. Run `terraform apply`, which will likely return an error indicating you need to verify the email address.
1. Verify the email address by clicking the link in the verification email that should have been sent after the previous step.
1. Run `terraform apply` again, which should be successful this time
