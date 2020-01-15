# Portal for Mass PFML

This is a [Next.js](https://nextjs.org/docs)-powered React app to bootstrap the Massachusetts Paid Family
and Medical Leave Portal.

## Prerequisites

Node v10 (or greater)

## Run

Run locally with:
```
npm install
npm run dev
```

## Local commands

### `npm test`

Runs the project's [test suite](../docs/tests.md).

### `npm run test:update-snapshot`

Updates _all_ [Jest snapshots](../docs/tests.md#Snapshot%20tests), accepting any updates as expected changes.

### `npm run test:watch`

Runs the project's test suite in watch mode. By default, this will attempt to identify which tests to run based on which files have changed in the current repository. After running, you can interact with the prompt to configure or filter which test files are ran.