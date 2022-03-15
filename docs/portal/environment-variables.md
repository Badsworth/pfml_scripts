# Environment variables

Environment variables include [feature flags](feature-flags.md), [maintenance pages](maintenance-pages.md), and URLs and keys for external resources such as Cognito and the API.

## Configuring environment variables

Default environment variables live in [`portal/config/default.js`](../../portal/config/default.js).

Each environment has a corresponding configuration file in [`portal/config`](../../portal/config/), for example `prod.js`

The default environment variables are merged with the environment-specific config file in [`portal/config/index.js`](../../portal/config/index.js). A default environment variable can be overridden in the environment-specific config file.

- **Portal environment variables should never include a secret!** Since the Portal is only served on the client-side, these environment variables will be publicly accessible.
- Environment variable values must be strings.
- Each time you add a new environment variable, ensure that you add it to each environment's config file, so that an environment isn't missing anything. If the variable value is shared across many environments, consider adding it as a default environment variable in [`portal/config/default.js`](../../portal/config/default.js).

## Referencing an environment variable

Within our codebase, environment variables are referenced from `process.env`. For example:

```js
Amplify.config(process.env.myCustomKey);
```

## How it works

The target environment is set as the `BUILD_ENV`. For example:

```
BUILD_ENV=stage npm run build
```

When the build script is ran, the contents of the configuration file corresponding to `BUILD_ENV` are assigned to the [Next.js `env` config option](https://nextjs.org/docs/api-reference/next.config.js/environment-variables) in [`portal/next.config.js`](../../portal/next.config.js). Next.js replaces `process.env` references with their values at build time.

### NODE_ENV

The `NODE_ENV` environment variable is automatically set by Next.js during development and builds. For our test scripts, we manually set this in the test's NPM scripts.

This variable determines whether our JS bundle includes the [production build of React or the dev build](https://reactjs.org/docs/optimizing-performance.html#use-the-production-build).

- When our NPM scripts call `next dev`, `NODE_ENV` is automatically set to `development` and our JS bundle includes the React development build.
- When our NPM scripts call `next build`, `NODE_ENV` is automatically set to `production` and our JS bundle includes the optimized React production build.

The `NODE_ENV` variable is also exposed to our code for use, allowing us to conditionally enable behavior for an environment, like only logging warnings when in `development`.

## Related

- [Portal Configuration Management](https://lwd.atlassian.net/wiki/spaces/DD/pages/304152764/Portal+Configuration+Management)
