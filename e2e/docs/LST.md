Load and Stress Testing
=======================

For load and stress testing, we use a tool called [Element](https://element.flood.io/). Element allows us to run browser-based load tests, which is necessary for interacting with Fineos.

One limitation we have with our load test tooling is that Element _cannot_ use any third party node modules - when we run our load tests in the cloud, it will fail catastrophically if it depends on any other modules. We're investigating ways to work around that, but for the time being, all Element code is kept separate from the rest of our codebase in `src/flood`.

In this project, we have set up our load tests to use "presets": a concept we created to specify data generation settings (scenario, count), and traffic profile settings (concurrency, duration). Presets may combine one or more separate tests.  For example our `basePlus` preset runs Portal claim submission traffic at the same time as Agent traffic. See our [preset configuration](../src/commands/flood/preset.config.ts) for more information.

Local Development of Tests
--------------------------

Before you can run a test locally, you must generate data.  To do that, run:
```shell
 E2E_ENVIRONMENT=performance npm run cli -- flood [presetId]
```
This will generate the necessary data for the preset you are running.  Next, start Element by running:
```shell
node_modules/.bin/element run src/flood/index.perf.ts --no-headless
```
This will open a Chrome window, and the test will execute.

Cloud Test Runs
---------------

When you are ready to run at scale, you can deploy to Flood.io using the following command:
```shell
 E2E_ENVIRONMENT=performance npm run cli -- flood [presetId] --deploy
```

This will run through the following steps for your preset:

1. Generate fresh data.
2. "Bundle" the typescript files (zips up the `src/flood` directory and makes a modified copy of `index.perf.ts`).
3. Use the Flood API to upload the bundle and invoke as many load tests as are needed for the selected preset.
