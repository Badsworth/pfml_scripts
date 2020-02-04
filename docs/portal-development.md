# Portal Development

This page covers development practices for working on the Mass PFML front-end portal. Please document liberally so that others may benefit from your learning.

## Configuration

Configuration environment is selected with the `BUILD_ENV` variable in [`portal/next.config.js`](../portal/next.config.js). Environment config files with variables are checked in under [`infra/portal_config/`](../infra/portal_config/). `dev` configs are used by default.

Use environment specific scripts to bundle builds with the correct configuration. See e.g. `build:test`, in [`portal/package.json`](../portal/package.json). Use `process.env.[ENV_VARIABLE_NAME]` to access config values.

### All Environments

There are currently two environments: `dev` and `test`. `dev` is meant for local development, and `test` is a stable pre-staging pre-production build.

### Adding an environment

To add other environments (e.g. `staging` or `prod`):

* Add the variables to a file named after the environment, e.g. `infra/portal_config/prod.js`.
* Update the environment lists in these docs.

## Creating a page

All files in the `portal/pages/` directory are automatically available as routes based on their name, e.g. `about.js` is routed to `/about`. Files named `index.js` are routed to the root of the directory. See more at the Next.js docs on [routing](https://nextjs.org/docs/routing/introduction) and [pages](https://nextjs.org/docs/basic-features/pages).

Each time you add a new page, update the `exportPathMap` in `next.config.js`. Without this, static HTML routing will not include the new page.

## Custom advanced behavior via `next.config.js`

The [`next.config.js`](https://nextjs.org/docs/api-reference/next.config.js/introduction) file is a Node.js module that can be used to configure advanced behavior, such as Webpack settings. Route exporting also lives here.
