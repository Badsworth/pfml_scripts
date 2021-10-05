/**
 * This file contains the custom New Relic reporter.
 *
 * It is written in JS because it's required directly by Cypress, not transpiled.
 */
/* eslint-disable @typescript-eslint/no-var-requires */
const { Runner, reporters, Suite } = require("mocha");
const fetch = require("node-fetch");
const debug = require("debug")("cypress:reporter:newrelic");
const { getRunMetadata } = require("./new-relic-collect-metadata");

module.exports = class NewRelicCypressReporter extends reporters.Spec {
  constructor(runner, options) {
    super(runner, options);

    const { accountId, apiKey, environment } = options.reporterOptions;
    this.accountId = accountId;
    this.apiKey = apiKey;
    this.environment = environment;
    this.queue = [];

    // Very important: Throw no errors here, as they have the potential to hang tests.
    if (!accountId)
      return console.warn(`New Relic Reporter: Unable to determine accountId.`);
    if (!apiKey)
      return console.warn(`New Relic Reporter: Unable to determine apiKey.`);
    debug("Booting New Relic Reporter");

    runner.on(Runner.constants.EVENT_TEST_END, (test) => {
      const promise = this.reportTest(test)
        .then(() => debug("Sent result to New Relic"))
        // Important - we absolutely cannot throw a real error here, or it will
        // stop the whole test.
        .catch((e) => console.error(e));
      this.queue.push(promise);
    });
  }
  async reportTest(test) {
    const suite = getSuite(test);
    const { ciBuildId: runId, group, tag, runUrl } = await getRunMetadata();
    const { environment } = this;
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
      schemaVersion: 0.2,
      environment,
      group,
      // @todo: Would we be better off treating this as an array?
      tag: tag ? tag.join(",") : "",
      runUrl,
    };
    if (test.err) {
      event.errorMessage = test.err.message;
      event.errorClass = test.err.name ?? "Error";
    }
    return this.send(event);
  }
  async send(event) {
    const { accountId, apiKey } = this;
    debug("Pushing custom event to New Relic", event);

    try {
      const res = await fetch(
        `https://insights-collector.newrelic.com/v1/accounts/${accountId}/events`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Api-Key": apiKey,
          },
          body: JSON.stringify(event),
        }
      );
      if (res.ok) {
        return;
      }
      return Promise.reject(
        `New Relic responded to a custom event push with a ${res.status} (${res.statusText}).`
      );
    } catch (e) {
      return Promise.reject(
        `New Relic reporter received an error while attempting to report a result: ${e}`
      );
    }
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
