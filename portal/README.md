# Portal for Mass PFML

This is a [Next.js](https://nextjs.org/docs)-powered React app to bootstrap the Massachusetts Paid Family and Medical Leave Portal.

**You may also be interested in:**

- [Setting up project tooling](../README.md)
- [Development practices](../docs/contributing.md)
- [Portal software architecture design](../docs/portal/software-architecture.md)
- [Additional Portal-specific documentation](../docs/portal/)

## Prerequisites

- Node v15 (or greater)
- NPM v7 (or greater)

## Env Configuration

Non-secret environment configuration is stored in [config/](config/) in files by env (`stage`, `test`, etc.)

## Local development

Install dependencies:

```
npm install
```

Run the development server with live reloading:

```
npm run dev
```

### Configure your code editor

- [Integrate ESLint into your IDE or a git hook](https://eslint.org/docs/user-guide/integrations) if you'd like to catch linting errors before it reaches the CI.
- [Setup your IDE to run Prettier upon save.](https://prettier.io/docs/en/editors.html)

## Build and Export the static site

In deployed environments, this app is served as static pages.

To build and export the site:

```
npm run build
```

To run the exported site:

```
npm start
```

Or serve using your favorite static server (e.g. [serve](https://www.npmjs.com/package/serve)) by passing in the static file directory `out` and an optional port flag (it defaults to `5000`):

```
serve out -p 8000
```

Or navigating to that directory:

```
cd out && serve
```

## Test commands

### `npm test`

Runs the project's [test suite](../docs/portal/tests.md), for unit tests on React components and JS files.

### `npm run test:update-snapshots`

Updates _all_ [Jest snapshots](../docs/portal/tests.md#Snapshot%20tests), accepting any updates as expected changes.

### `npm run test:watch`

Runs the project's test suite in watch mode. By default, this will attempt to identify which tests to run based on which files have changed in the current repository. After running, you can interact with the prompt to configure or filter which test files are ran.

## Design tooling commands

### `npm run docs`

Run the UI component explorer sandbox, [Storybook](https://storybook.js.org/). A new browser window should automatically open with the explorer loaded once this script has completed running. It may take a minute or so to load on initial run. [Read more about how we're using Storybook.](../docs/portal/storybook.md)

### `npm run docs:build`

Exports the Storybook site as a static HTML site.

## Additional commands

### `npm run format`

Automatically format files using [Prettier](https://prettier.io/).

This can be ran in a pull request by adding a comment with a body of:

```
/gh portal format
```

### `npm run lint`

Run ESLint. Fixes any [auto-fixable ESLint errors](https://eslint.org/docs/user-guide/command-line-interface#fixing-problems).

#### `npm run lint:ci`

Runs ESLint and fails on errors. Does not attempt to auto-fix ESLint errors.

### `npm run analyze-bundle`

Runs `webpack-bundle-analyzer` over the Next.js build, scanning the bundle and creating a visualization of what’s inside it. This can be helpful to debug the bundle size. Use this visualization to find large or unnecessary dependencies.

After the script fully runs, it should have opened two browser tabs: `server.html` and `client.html`. The one for the browser bundle, `client.html`, is the one relevant to our project since we are exporting only the static browser bundle.

#### What to look for

By default, the stats page shows the size of parsed files (i.e., of files as they appear in the bundle). You’ll likely want to compare gzip sizes since that’s closer to what real users experience; use the sidebar on the left to switch the sizes.

Here’s what to look for in the report:

- Large dependencies. Why are they so large? Are there smaller alternatives? Do you use all the code it includes?
- Duplicated dependencies. Do you see the same library repeating in multiple files? Or does the bundle have multiple versions of the same library?
- Similar dependencies. Are there similar libraries that do approximately the same job? Try sticking with a single tool.

Check out [this post](https://medium.com/webpack/webpack-bits-getting-the-most-out-of-the-commonschunkplugin-ab389e5f318) for an example of how a Webpack contributor used the bundle analyzer.

## Releases

More details about how to handle releases are available in the [release
runbook](https://lwd.atlassian.net/wiki/spaces/DD/pages/818184193/API+and+Portal+Runbook).

As a part of the release process it is useful to include some technical notes on
what the release includes. There is a make target to help automate some of this:

```sh
make release-notes
```

This will generate a list of the commits impacting a PORTAL release. For the
commits that follow the project convention for commit messages, the Jira ticket
will be linked. Everyone does not follow the convention nor will every commit
have a Jira ticket associated.

But this will provide a starting point. By default it will generate the list of
commits that are different between what is deployed to stage (indicated by the
`deploy/portal/stage` branch) and what is on `main`. You can change the range of
commits it considers by passing in `refs`, for example only looking for changes
between release candidates:

```sh
make release-notes refs="portal/v6.1..portal/v7.0"
```

The work will generally fall into one of a number of categories, with changes to:

- EMPLOYER
- INFRA
- CP

It's useful to group the release notes broadly by these buckets to clarify what
this particular release will impact.

It's also usually useful to group the tickets by team, which piping to `sort`
can help facilitate:

```sh
make release-notes | sort
```

Ultimately culminating in something like the notes for
[api/v1.3.0](https://github.com/EOLWD/pfml/releases/tag/api%2Fv1.3.0).

## Figuring out what's released where

There are a couple other make targets that could be useful. Note these all work
off of your local git repo, so can only be as accurate as your local checkout
is. You will generally want to run `git fetch origin` before these if you want
the most up-to-date info.

`where-ticket` will search the release branches for references to the provided
ticket number:

```sh
❯ make where-ticket ticket=CP-1709
## origin/main ##
3894541e CP-1701: add tel link to Contact Center phone numbers (#2818)

## origin/deploy/portal/stage ##
3894541e CP-1701: add tel link to Contact Center phone numbers (#2818)

## origin/deploy/portal/prod ##

## origin/deploy/portal/performance ##
3894541e CP-1701: add tel link to Contact Center phone numbers (#2818)

## origin/deploy/portal/training ##

## origin/deploy/portal/uat ##
3894541e CP-1701: add tel link to Contact Center phone numbers (#2818)

```

So in this example, CP-1709 has been deployed to every environment but `training` and `prod`.

`whats-released` lists some info about the lastest commits on the release branches:

```sh
❯ make whats-released
## origin/main ##
 * Closest tag: portal/v7.0-38-g6316145e
 * Latest commit: 6316145e (origin/main, origin/HEAD, main) Change resource_arn and web_acl_id references (#3035)

## origin/deploy/portal/stage ##
 * Closest tag: portal/v7.0
 * Latest commit: 271323e8 (tag: portal/v7.0, origin/release/portal/v7.0, origin/deploy/portal/uat, origin/deploy/portal/stage, origin/deploy/portal/performance) API-1331: Explicitly set UUID for payment object in FINEOS payment processing code. (#2981)

## origin/deploy/portal/prod ##
 * Closest tag: portal/v6.0
 * Latest commit: 64a18db5 (tag: portal/v6.0-rc2, tag: portal/v6.0, origin/deploy/portal/training, origin/deploy/portal/prod) INFRA-186: Add scheduler config for payments-fineos-process (#2792)

## origin/deploy/portal/performance ##
 * Closest tag: portal/v7.0
 * Latest commit: 271323e8 (tag: portal/v7.0, origin/release/portal/v7.0, origin/deploy/portal/uat, origin/deploy/portal/stage, origin/deploy/portal/performance) API-1331: Explicitly set UUID for payment object in FINEOS payment processing code. (#2981)

## origin/deploy/portal/training ##
 * Closest tag: portal/v6.0
 * Latest commit: 64a18db5 (tag: portal/v6.0-rc2, tag: portal/v6.0, origin/deploy/portal/training, origin/deploy/portal/prod) INFRA-186: Add scheduler config for payments-fineos-process (#2792)

## origin/deploy/portal/uat ##
 * Closest tag: portal/v7.0
 * Latest commit: 271323e8 (tag: portal/v7.0, origin/release/portal/v7.0, origin/deploy/portal/uat, origin/deploy/portal/stage, origin/deploy/portal/performance) API-1331: Explicitly set UUID for payment object in FINEOS payment processing code. (#2981)
```

## Directory Structure

Below is an abbreviated representation of our directory structure, pointing out some of the main files to get you started. Refer to [`software-architecture.md`](../docs/portal/software-architecture.md) for more context.

```
├── __mocks__               Dependency mocks used by test suites
├── tests                   Test suites
├── config                  Env. variables & feature flags
├── public                  Static assets
├── src                     Source code
│   ├── api                 API request modules
│   ├── components
│   │   └── PageWrapper.js  🖼 Main layout applied to all pages
│   ├── hooks               Custom React hooks
│   ├── locales             Localization files
│   ├── models              Data models
│   ├── pages
│   │   ├── _app.js         ⭐️ Entry point, setting up the entire application
│   │   ├── applications    Pages for authenticated claimants
│   │   │   └── index.js    List of applications for claimants
│   │   ├── employers       Pages for authenticated employers
│   │   │   └── index.js    Dashboard for authenticated employers
│   │   └── index.js        Landing page for unauthenticated users
│   ├── services
│   └── utils               Utility functions
├── storybook               Storybook site config and stories
├── styles
│   └── app.scss            Main stylesheet
└── next.config.js          Build process config for Portal
```
