# Portal for Mass PFML

This is a [Next.js](https://nextjs.org/docs)-powered React app to bootstrap the Massachusetts Paid Family and Medical Leave Portal.

**You may also be interested in:**

- [Setting up project tooling](../README.md)
- [Development practices](../docs/contributing.md)
- [Additional Portal-specific documentation](../docs/portal/)

## Environments

- [Test](https://pfml-sandbox-v2.navateam.com/)

## Prerequisites

Node v10 (or greater)

## Env Configuration

Non-secret environment configuration is stored in [infra/portal/config/](../infra/portal/config/) in files by env (`dev`, `test`, etc.)

## Local development

Install dependencies:

```
npm install
```

Run the development server with live reloading:

```
npm run dev
```

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

## Additional commands

### `npm run docs`

Run the UI component explorer sandbox, [Storybook](https://storybook.js.org/). A new browser window should automatically open with the explorer loaded once this script has completed running. It may take a minute or so to load on initial run.

### `npm test`

Runs the project's [test suite](../docs/portal/tests.md).

### `npm run test:update-snapshots`

Updates _all_ [Jest snapshots](../docs/portal/tests.md#Snapshot%20tests), accepting any updates as expected changes.

### `npm run test:watch`

Runs the project's test suite in watch mode. By default, this will attempt to identify which tests to run based on which files have changed in the current repository. After running, you can interact with the prompt to configure or filter which test files are ran.

## Directory Structure

Below is an abbreviated representation of our directory structure, pointing out some of the main files to get you started:

```
├── __tests__           Test suites
├── config
|   └── featureFlags.js Default feature flag values for each environment
├── public              Static assets
├── src                 Source code
|   ├── actions
|   |   └── index.js    Redux actions
│   ├── components
│   ├── locales         Localization files
│   │   └── i18n.js     Internationalization setup
|   ├── pages
│   │   ├── _app.js     Main layout applied to all pages
│   │   └── index.js    Homepage
|   ├── reducers        Redux reducers
|   ├── utils           utility functions
|   ├── store.js        Redux store initialization method
├── styles
│   └── app.scss        Main stylesheet
└── next.config.js      Build process config
```
