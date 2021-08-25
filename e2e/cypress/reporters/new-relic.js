/**
 * This file contains the custom New Relic reporter.
 *
 * It is written in JS because it's required directly by Cypress, not transpiled.
 */
/* eslint-disable @typescript-eslint/no-var-requires */
const { parse } = require("yargs");
const { Runner, reporters, Suite } = require("mocha");
const fetch = require("node-fetch");
const debug = require("debug")("cypress:reporter:newrelic");

module.exports = class NewRelicCypressReporter extends reporters.Spec {
  constructor(runner, options) {
    super(runner, options);

    const { accountId, apiKey, environment } = options.reporterOptions;
    // Parse the Cypress input to determine group, ci-build-id, etc. This is
    // pretty dirty, but there's no other way to get at this information.
    // Strip off the -- argument, which prevents us from parsing further args.
    const args = parse(process.argv.filter((a) => a !== "--"));
    const { group, tag, ciBuildId } = args;

    // Very important: Throw no errors here, as they have the potential to hang tests.
    if (!ciBuildId)
      return console.warn(`New Relic Reporter: Unable to determine ciBuildId.`);
    if (!accountId)
      return console.warn(`New Relic Reporter: Unable to determine accountId.`);
    if (!apiKey)
      return console.warn(`New Relic Reporter: Unable to determine apiKey.`);
    debug("Booting New Relic Reporter");

    console.log(
      `Reporting New Relic results with the following runId: ${ciBuildId}`
    );
    this.queue = [];
    runner.once(Runner.constants.EVENT_TEST_END, (test) => {
      const suite = getSuite(test);
      const event = {
        runId: ciBuildId,
        eventType: "CypressTestResult",
        test: test.title,
        suite: suite.title,
        file: getSuiteWithFile(suite),
        status: test.state,
        durationMs: test.duration ?? 0,
        pass: test.state === "passed",
        flaky: test.state === "passed" && test._currentRetry > 0,
        schemaVersion: 0.2,
        environment,
        group,
        tag,
      };
      if (test.err) {
        event.errorMessage = test.err.message;
        event.errorClass = test.err.name ?? "Error";
      }

      debug("Pushing custom event to New Relic", event);
      const prom = fetch(
        `https://insights-collector.newrelic.com/v1/accounts/${accountId}/events`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Api-Key": apiKey,
          },
          body: JSON.stringify(event),
        }
      )
        .then((res) => {
          if (!res.ok) {
            return Promise.reject(
              `New Relic responded to a custom event push with a ${res.status} (${res.statusText}).`
            );
          }
          debug("Received OK response from New Relic");
          return event;
        })
        // Do not allow this promise to reject uncaught. Rejected promises thrown by reporters
        // will result in a failure to record the test run in the dashboard. Instead, swallow the
        // error and move on.
        .catch((e) => {
          console.error(
            `New Relic reporter received an error while attempting to report a result: ${e}`
          );
        });
      // const prom = Promise.resolve(event);
      this.queue.push(prom);
    });
  }
  done(failures, fn) {
    // Wait for all write promises to complete.
    if (this.queue.length) {
      Promise.all(this.queue).then(() => fn(failures));
      return;
    }
    fn(failures);
  }
};

function getSuite(testOrSuite) {
  if (testOrSuite instanceof Suite) {
    return testOrSuite;
  }
  if (testOrSuite.parent) {
    return getSuite(testOrSuite.parent);
  }
  console.warn("Unable to determine parent suite");
  return testOrSuite;
}

function getSuiteWithFile(suite) {
  if (suite.file) {
    return suite.file;
  }
  if (suite.parent) {
    return getSuiteWithFile(suite.parent);
  }
  console.warn("Unable to find file for suite");
  return "UNKNOWN";
}
