# Environment variables

Environment variables include [feature flags](feature-flags.md), URLs and keys for external resources such as Cognito and the API.

Each Portal environment has a configuration file in [`portal/config`](../portal/config/). An important piece to note here is that since the Portal is only served on the client-side, application configuration files do not include secrets.

Within our codebase, environment variables are referenced from `process.env`. For example:

```
Amplify.config(process.env.customKey)
```

During the build process, the target environment is set as the `BUILD_ENV`

For example:

```
BUILD_ENV=test npm run build
```

We use environment specific NPM scripts in [`portal/package.json`](../portal/package.json) to bundle builds with the correct configuration.

The corresponding configuration file’s contents are assigned to the [Next.js `env` config option](https://nextjs.org/docs/api-reference/next.config.js/environment-variables) in [`portal/next.config.js`](../portal/next.config.js). Next.js replaces `process.env` references with their values at build time.

## Related

- [Portal Configuration Management](https://lwd.atlassian.net/wiki/spaces/DD/pages/304152764/Portal+Configuration+Management)
