# Portal for Mass PFML

This is a [Next.js](https://nextjs.org/docs)-powered React app to bootstrap the Massachusetts Paid Family and Medical Leave Portal.

**You may also be interested in:**

- [Setting up project tooling](../README.md)
- [Development practices](../docs/contributing.md)
- [Portal software architecture design](../docs/portal/software-architecture.md)
- [Additional Portal-specific documentation](../docs/portal/)

## Environments

- [Test](https://d1ah9hpoapx4f1.cloudfront.net/)

## Prerequisites

Node v10 (or greater)

## Env Configuration

Non-secret environment configuration is stored in [config/](config/) in files by env (`stage`, `test`, etc.)

## Local development

Install dependencies:

> This script will install a number of large developer dependencies, so may take awhile when you first run this. Since we use `puppeteer` for headless browser tests, this downloads a recent version of Chromium (~170MB Mac, ~282MB Linux) that is guaranteed to work with the Puppeteer API. You can skip the Chromium download by setting the `PUPPETEER_SKIP_CHROMIUM_DOWNLOAD` [environment variable](https://github.com/puppeteer/puppeteer/blob/master/docs/api.md#environment-variables).

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

### `npm run docs`

Run the UI component explorer sandbox, [Storybook](https://storybook.js.org/). A new browser window should automatically open with the explorer loaded once this script has completed running. It may take a minute or so to load on initial run.

### `npm test`

Runs the project's [test suite](../docs/portal/tests.md), for unit tests on React components and JS files.

### `npm test:e2e`

Runs the project's [test suite](../docs/portal/tests.md), for end-to-end tests in a headless browser.

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
