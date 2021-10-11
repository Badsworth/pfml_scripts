# e2e-dashboard

Dashboard which should allow the members of PFML project to see at a glance the state of lower environments as described by the results of running the E2E test suite.

## Epic

**[PFMLPB-1999](https://lwd.atlassian.net/browse/PFMLPB-1999)**

## Getting started

1. [Set up nr1 CLI](https://one.newrelic.com/launcher/developer-center.launcher?pane=eyJuZXJkbGV0SWQiOiJkZXZlbG9wZXItY2VudGVyLmRldmVsb3Blci1jZW50ZXIifQ==)(no need to go through steps 5 & 6)
2. Run the following scripts:

```
npm install
npm start
```

This package is based on the source code from [nr1-status-widgets](https://github.com/newrelic/nr1-status-widgets) repo. It's a good place to start for inspiration.

Visit https://one.newrelic.com/?nerdpacks=local and :sparkles:

## Useful Links

1. [nr1 CLI reference](https://developer.newrelic.com/explore-docs/nr1-cli/)
2. [New Relic SKD component docs](https://developer.newrelic.com/explore-docs/intro-to-sdk/)
3. [Visualization config](https://developer.newrelic.com/explore-docs/custom-viz/configuration-options/) vs [Nerdlet config](https://developer.newrelic.com/explore-docs/nerdpack-file-structure/#nr1json)

## Creating new artifacts

If you want to create new artifacts run the following command:

```
nr1 create
```

> Example: `nr1 create --type nerdlet --name my-nerdlet`.

### Whats a nerdlet?

Nerdlet is just a react component, it can receive the current state of the NR client via the `PlatformStateContext` component. Platform state includes date-time, query start & end timestamps, current query parameters, etc.
You can set those in New Relic interface like this:
![image](https://user-images.githubusercontent.com/55783724/136820670-231d83ad-730d-4cb7-9022-95fa763f5794.png)

### What's a visualization?

Visualization is different type of nerdlet, it has the `"schemaType"` of `"VISUALIZATION"` set in `nr1.json`,
and can have a property of `configuration` in `nr1.json`, describing the configuration which can be set for it directly by the user.
You can see how it's set here: ![image](https://user-images.githubusercontent.com/55783724/136821446-379be761-6864-4a6a-9310-b5100e876b94.png)

The configuration is passed directly to your root visualization component in it's `props`.
