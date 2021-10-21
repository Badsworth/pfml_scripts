# PFML New Relic Nerdpack

This package contains display-related components for New Relic monitoring.

## Getting started

1. [Install and configure the NR1 CLI](https://developer.newrelic.com/build-apps/ab-test/install-nr1/).
2. Run the following commands:
   ```shell
   npm install
   npm start
   ```

This will start development mode and output a link you can use to view the dashboard locally.

## Creating new artifacts

If you want to create new artifacts run the following command:

```
nr1 create
```

> Example: `nr1 create --type nerdlet --name my-nerdlet`.

## Publishing a new version

When we are satisfied with changes and ready to publish a new version, this can be done by:

1. Bump the `version` string `e2e/nerdpack/package.json` to a new version (eg: 1.0.2 -> 1.0.3).
2. Run `nr1 nerdpack:publish` to bundle the code and push to New Relic.
