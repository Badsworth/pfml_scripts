/**
 * This file contains the custom New Relic reporter.
 *
 * It is written in JS because it's required directly by Cypress, not transpiled.
 */
/* eslint-disable @typescript-eslint/no-var-requires */
const { Runner, reporters, Suite } = require("mocha");
const fetch = require("node-fetch");
const debug = require("debug")("cypress:reporter:newrelic");

module.exports = class NewRelicCypressReporter extends reporters.Base {
  constructor(runner, options) {
    super(runner, options);

    const { accountId, apiKey, runId, environment, group, tag } =
      options.reporterOptions;
    if (!runId)
      throw new Error(`New Relic Reporter: Unable to determine runId.`);
    if (!accountId)
      throw new Error(`New Relic Reporter: Unable to determine accountId.`);
    if (!apiKey)
      throw new Error(`New Relic Reporter: Unable to determine apiKey.`);
    if (!environment)
      throw new Error(`New Relic Reporter: Unable to determine environment.`);
    debug("Booting New Relic Reporter");

    console.log(`Reporting New Relic results with the following runId: ${runId}`);
    this.queue = [];
    runner.once(Runner.constants.EVENT_TEST_END, (test) => {
      const suite = getSuite(test);
      const event = {
        runId,
        eventType: "CypressTestResult",
        test: test.title,
        suite: suite.title,
        file: getSuiteWithFile(suite),
        status: test.state,
        durationMs: test.duration ?? 0,
        pass: test.state === "passed",
        flaky: test.state === "passed" && test._currentRetry > 0,
        schemaVersion: 0.1,
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
      ).then((res) => {
        if (!res.ok) {
          return Promise.reject(
            `New Relic responded to a custom event push with a ${res.status} (${res.statusText}).`
          );
        }
        debug("Received OK response from New Relic");
        return event;
      });
      // const prom = Promise.resolve(event);
      this.queue.push(prom);
    });
  }
  done(failures, fn) {
    // Wait for all write promises to complete.
    if (this.queue.length) {
      Promise.all(this.queue)
        .then(() => fn(failures))
        .catch((e) => {
          console.error(e);
          fn(failures);
        });
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
  throw new Error("Unable to determine parent suite");
}

function getSuiteWithFile(suite) {
  if (suite.file) {
    return suite.file;
  }
  if (suite.parent) {
    return getSuiteWithFile(suite.parent);
  }
  throw new Error("Unable to find file for suite");
}
