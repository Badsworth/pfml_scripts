/* eslint-env node */
const fetch = require("node-fetch");
const path = require("path");

// Get NR credentials from env
const accountId = process.env.E2E_NEWRELIC_ACCOUNTID;
const apiKey = process.env.E2E_NEWRELIC_INGEST_KEY;

// Our reporter implements only the onRunComplete lifecycle
// function, run after all tests have completed
class CustomReporter {
  static MAX_NR_CUSTOM_FIELD_LENGTH = 4096;

  getLegacyTestResult(file, res) {
    const event = {
      runId: process.env.TEST_RUN_ID,
      branch: path.relative("refs/heads", process.env.GITHUB_REF),
      environment: process.env.E2E_ENVIRONMENT,
      eventType: "IntegrationTestResult",
      file: file.testFilePath.split("e2e/")[1],
      specStart: file.perfStats.start,
      specEnd: file.perfStats.end,
      specRuntime: file.perfStats.runtime,
      passed: res.status === "passed",
      status: res.status,
      fullName: res.fullName,
      durationMs: res.duration,
      title: res.title,
      errorMessage: this.getErrorMessage(res),
      // res.invocations contains the number of times this block was run
      // If it's more than 1 - it was retried.
      flaky: res.status === "passed" && res.invocations > 1,
      suite: res.ancestorTitles.join(" "),
    };
    // If there was an error thrown during a test which isn't handled by the test itself
    // Set error details
    if (res.testExecError) {
      event.errorCode = res.testExecError.code;
      event.errorMessage = res.testExecError.message;
      event.errorStack = res.testExecError.stack;
      event.errorType = res.testExecError.type;
    }
    return event;
  }

  getTestResultRunUrl() {
    if (
      !process.env.GITHUB_SERVER_URL ||
      !process.env.GITHUB_REPOSITORY ||
      !process.env.GITHUB_RUN_ID
    ) {
      return "";
    }
    return `${process.env.GITHUB_SERVER_URL}/${process.env.GITHUB_REPOSITORY}/actions/runs/${process.env.GITHUB_RUN_ID}?check_suite_focus=true`;
  }

  getErrorMessage(result) {
    const fullErrorMessage = result.failureMessages.join("|");
    return fullErrorMessage.slice(
      0,
      Math.min(fullErrorMessage.length, this.MAX_NR_CUSTOM_FIELD_LENGTH)
    );
  }

  getTestResult(file, result) {
    return {
      eventType: "TestResult",
      runId: process.env.TEST_RUN_ID,
      runUrl: this.getTestResultRunUrl(),
      environment: process.env.E2E_ENVIRONMENT,
      branch: path.relative("refs/heads", process.env.GITHUB_REF),
      file: file.testFilePath.split("e2e/")[1],
      blockTitle: result.title,
      duration: result.duration,
      status: result.status,
      tag: "",
      tagGroup: "",
      group: "Integration",
      pass: result.status === "passed",
      fail: result.status === "failed",
      skip: result.status === "pending",
      flaky: result.status === "passed" && result.invocations > 1,
    };
  }

  getTestResultInstance(test, result) {
    return {
      eventType: "TestResultInstance",
      runId: process.env.TEST_RUN_ID,
      runUrl: this.getTestResultRunUrl(),
      environment: process.env.E2E_ENVIRONMENT,
      branch: path.relative("refs/heads", process.env.GITHUB_REF),
      file: test.path.split("e2e/")[1],
      blockTitle: result.title,
      duration: result.duration,
      tryNumber: result.invocations,
      tag: "",
      tagGroup: "",
      group: "Integration",
      status: result.status,
      pass: result.status === "passed",
      fail: result.status === "failed",
      skip: result.status === "pending",
      anonymizedMessage: this.getErrorMessage(result),
    };
  }

  async onTestCaseResult(test, result) {
    await pushEventToNewRelic(this.getTestResultInstance(test, result));
  }

  async onRunComplete(_, aggregateResult) {
    const events = [];
    // Aggregate result has results for tests in each file
    aggregateResult.testResults.forEach((file) => {
      // Those have results per `it` or `test` block.
      file.testResults.forEach((res) => {
        events.push(this.getLegacyTestResult(file, res));
        events.push(this.getTestResult(file, res));
      });
    });
    return await Promise.all(events.map(pushEventToNewRelic));
  }
}

function pushEventToNewRelic(event) {
  return fetch(
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
      return event;
    })
    .catch((e) => {
      console.error(
        `New Relic reporter received an error while attempting to report a result: ${e}`
      );
    });
}

module.exports = CustomReporter;
