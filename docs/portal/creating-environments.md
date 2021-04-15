# Setting up a new environment

This docs covers the steps you need to take to configure the Portal web app to support a new environment.

Before reading this, make sure you've already ran through the [steps to setup the infrastructure for a new environment](../creating-environments.md).

## Add environment variables

1. Create a new config file for the environment in [`portal/config`](../../portal/config), copying the properties from another environment.
1. Update the variables for the environment. Primarily, you'll want to update the environment name and the Cognito IDs, which should have been output after you ran `terraform apply` e.g.:

   ```
   module.massgov_pfml.aws_cognito_user_pool.claimants_pool: Creation complete after 2s [id=us-east-1_Bi6tPV5hz]
   ...
   module.massgov_pfml.aws_cognito_user_pool_client.massgov_pfml_client: Creation complete after 0s [id=606qc6fmb1sn3pcujrav20h66l]
   ```

1. Set up a New Relic Browser app. Go to [New Relic](https://one.newrelic.com) > Add More Data > New Relic Browser.

   - Select Copy/Paste Javascript Code
   - Select Pro + SPA
   - Enable cookies and distributed tracing
   - Click CONTINUE
   - Copy _only the applicationId_ from the JS snippet and add it to the config file you created.

   See [Monitoring](./monitoring.md) and [Web Analytics](./web-analytics.md) READMEs for more details about how New Relic and Google Tag Manager are configured.

1. Add an entry for the new environment to [`portal/config/index.js`](../../portal/config/index.js), copying the properties from another environment.
1. Make sure the associated API environment's origin URL is listed in the list of `allowed_origins` in `new-relic.js`.

## Add a build script

Each environment should have its own build script in `portal/package.json` so that the site can be built using the correct environment variables. Refer to other build scripts, like `build:test` for an example.

## Update GitHub Actions

Each environment will have its own GitHub branch that will deploy when changes are pushed. Create a new deploy branch (e.g. `deploy/portal/breakfix`) and update the [deployment doc](../deployment.md) with details about deploying to the new environment.

Once all of this is set up, run a real deployment using the steps in [deployment](../deployment.md).
