/**
 * This file contains the custom New Relic reporter.
 *
 * It is written in JS because it's required directly by Cypress, not transpiled.
 */
const { Runner, reporters, Suite } = require("mocha");
const fetch = require("node-fetch");
const debug = require("debug")("cypress:reporter:newrelic");
const { getRunMetadata } = require("./new-relic-collect-metadata");
const { ErrorCategory } = require("./service/error-category.js");

module.exports = class NewRelicCypressReporter extends reporters.Spec {
  static MAX_NR_EVENT_LENGTH = 4096;

  constructor(runner, options) {
    super(runner, options);

    const { accountId, apiKey, environment, branch } = options.reporterOptions;
    this.accountId = accountId;
    this.apiKey = apiKey;
    this.environment = environment;
    this.branch = branch;
    this.queue = [];
    this.ErrorCategory = new ErrorCategory();

    // Very important: Throw no errors here, as they have the potential to hang tests.
    if (!accountId) {
      return console.warn(`New Relic Reporter: Unable to determine accountId.`);
    }
    if (!apiKey) {
      return console.warn(`New Relic Reporter: Unable to determine apiKey.`);
    }
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
    const metadata = await getRunMetadata();
    metadata.suite = getSuite(test);

    const events = this.buildTestResultInstances(metadata, test);
    events.push(this.buildTestResult(metadata, test));
    //@TODO: remove after dashboard V1 sunset
    events.push(this.buildCypressTestResult(metadata, test));
    return this.send(events);
  }

  /**
   *
   * @param metadata
   * @param test
   * @returns {Promise<{schemaVersion: number, test, pass: boolean, flaky: boolean, runUrl: *, eventType: string, branch: *, environment: *, suite: *, file: (*|string|string), runId: *, tag: (*|string), durationMs: number, status, group}>}
   */
  buildCypressTestResult(metadata, test) {
    const event = {
      runId: metadata.ciBuildId,
      branch: this.branch,
      eventType: "CypressTestResult",
      test: test.title,
      suite: metadata.suite.title,
      file: getSuiteWithFile(metadata.suite),
      status: test.state,
      durationMs: test.duration ?? 0,
      pass: test.state === "passed",
      flaky: test.state === "passed" && test._currentRetry > 0,
      schemaVersion: 0.2,
      environment: this.environment,
      group: metadata.group,
      tag: metadata.tag ? metadata.tag.join(",") : "",
      runUrl: metadata.runUrl,
    };

    // ADD Categorization system function here
    if (test.err) {
      event.errorClass = test.err.name ?? "Error";
      if (test.err.codeFrame && test.err.codeFrame.line) {
        event.errorLine = test.err.codeFrame.line;
      }
      if (test.err.codeFrame && test.err.codeFrame.relativeFile) {
        event.errorRelativeFile = test.err.codeFrame.relativeFile;
      }
      event.errorMessage = test.err.message;
      // custom attibute length is 4096 chars https://docs.newrelic.com/docs/data-apis/custom-data/custom-events/data-requirements-limits-custom-event-data/
      // Error messages could cause failures by posting an event by going over the NR character limit
      // to stay within these contraints, excess characters need to be sliced off
      if (
        event?.errorMessage &&
        event.errorMessage.length > this.MAX_NR_EVENT_LENGTH
      ) {
        const charsOver = event.errorMessage.length - this.MAX_NR_EVENT_LENGTH;
        event.errorMessage = event.errorMessage.slice(0, -charsOver);
      }
      this.ErrorCategory.setErrorCategory(event);
    }

    return event;
  }

  buildTestResult(metadata, test) {
    return {
      eventType: "TestResult",
      ...this.setEventCommon(metadata, test),
      ...this.setEventState(test),
      flaky: test.state === "passed" && test._currentRetry > 0,
    };
  }

  buildTestResultInstances(metadata, test) {
    const events = [];
    if (test?.prevAttempts && test.prevAttempts.length) {
      test.prevAttempts.forEach((attempt) => {
        events.push(
          this.buildTestResultInstance(
            metadata,
            test,
            attempt,
            events.length + 1
          )
        );
      });
    }
    events.push(
      this.buildTestResultInstance(metadata, test, null, events.length + 1)
    );
    return events;
  }

  buildTestResultInstance(metadata, test, attempt, tryNumber) {
    return {
      eventType: "TestResultInstance",
      ...this.setEventCommon(metadata, test),
      ...this.setEventState(attempt ? attempt : test),
      tryNumber: tryNumber,
      anonymizedMessage: this.getErrorMessage(attempt ? attempt : test),
      schemaVersion: 0.2,
    };
  }

  setEventCommon(metadata, test) {
    return {
      schemaVersion: 0.2,
      runId: metadata.ciBuildId,
      runUrl: metadata.runUrl,
      environment: this.environment,
      branch: this.branch,
      file: getSuiteWithFile(metadata.suite),
      blockTitle: test.title,
      duration: test.duration ?? 0,
      tag: metadata.tag ? metadata.tag.join(",") : "",
      group: metadata.group,
    };
  }

  setEventState(test) {
    return {
      status: test.state,
      pass: test.state === "passed",
      fail: test.state === "failed",
      skip: test.state === "pending",
    };
  }

  getErrorMessage(test) {
    let errorMessage = "";
    if (test.err) {
      errorMessage = this.getAnonymizedErrorMessage(test.err.message);
      // custom attibute length is 4096 chars https://docs.newrelic.com/docs/data-apis/custom-data/custom-events/data-requirements-limits-custom-event-data/
      // Error messages could cause failures by posting an event by going over the NR character limit
      // to stay within these contraints, excess characters need to be sliced off
      if (errorMessage.length > this.MAX_NR_EVENT_LENGTH) {
        const charsOver = errorMessage.length - this.MAX_NR_EVENT_LENGTH;
        errorMessage = errorMessage.slice(0, -charsOver);
      }
    }
    return errorMessage;
  }

  getAnonymizedErrorMessage(message) {
    return (
      message
        // Take off the "Timed out after retrying..." prefix. It's not helpful.
        .replace(/Timed out retrying after \d+ms: /g, "")
        // Anonymize UUIDs.
        .replace(
          /[\da-f]{8}-[\da-f]{4}-[\da-f]{4}-[\da-f]{4}-[\da-f]{12}/g,
          "XXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"
        )
        // Anonymize domains for portal, API and fineos.
        .replace(/paidleave-api-([a-z-]+)(\.dfml)?(\.eol)?\.mass\.gov/g, "api")
        .replace(/[a-z0-9]+.execute-api.us-east-1.amazonaws.com/g, "api")
        .replace(/\/api\/performance\/api/g, "/api/api")
        .replace(/paidleave-([a-z-]+)(\.eol)?\.mass\.gov/g, "portal")
        .replace(/[a-z0-9-]+-claims-webapp.masspfml.fineos.com/g, "fineos")
        // Anonymize NTNs, preserving the ABS/AP suffixes without their digits.
        .replace(/NTN-\d+/g, "NTN-XXX")
        .replace(/-(ABS|AP)-\d+/g, "-$1-XX")
        // Anonymize dates and times.
        .replace(/\d{2}\/\d{2}\/\d{4}/g, "XX/XX/XXXX") // Raw dates
        .replace(/\d{2}\\\/\d{2}\\\/\d{4}/g, "XX\\/XX\\/XXXX") // Regex formatted dates.
        .replace(/\d+ms/g, "Xms") // Milliseconds.
        .replace(/\d+ seconds/g, "X seconds")
        // Anomymize Fineos element selectors, which are prone to change (eg: SomethingWidget_un19_Something).
        .replace(/_un(\d+)_/g, "_unXX_")
        .replace(/_PL_\d+_\d+_/g, "_PL_X_X_")
        .replace(/__TE:\d+:\d+_/g, "__TE:X:X_")
        // Anonymize temp directories used by cy.stash().
        .replace(/\/tmp\/[\d-]+/g, "/tmp/XXX")
        // Drop excess Ajax request waiting data.
        .replace(/(In-flight Ajax requests should be 0).*/g, "$1")
        // Drop debug information...
        .split("Here are the matching elements:")[0]
        .split("Debug information")[0]
        .split("Debug Information")[0]
        .trim()
    );
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
