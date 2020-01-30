# Portal for Mass PFML

This is a [Next.js](https://nextjs.org/docs)-powered React app to bootstrap the Massachusetts Paid Family
and Medical Leave Portal.

## Prerequisites

Node v10 (or greater)

## Env Configuration

Environment configuration is stored in local files by env (`dev`, `test`, etc.), not checked in. See [Portal Development Environment Configuration](../docs/portal-development.md#Developer%20One-time%20Setup) for how to set up your local environment.

## Run

Run locally with:
```
npm install
npm run dev
```

## Export for static serving

In deployed environments, this app is served as static pages. To build and export the site:
```
npm run build
```

Serve using your favorite static server (e.g. [serve](https://www.npmjs.com/package/serve)) by passing in the static file directory `out` and an optional port flag (it defaults to `5000`):
```
serve out -p 8000
```

Or navigating to that directory:
```
cd out && serve
```

## Local commands

### `npm test`

Runs the project's [test suite](../docs/tests.md).

### `npm run test:update-snapshot`

Updates _all_ [Jest snapshots](../docs/tests.md#Snapshot%20tests), accepting any updates as expected changes.

### `npm run test:watch`

Runs the project's test suite in watch mode. By default, this will attempt to identify which tests to run based on which files have changed in the current repository. After running, you can interact with the prompt to configure or filter which test files are ran.
