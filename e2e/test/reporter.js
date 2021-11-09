/* eslint-env node */
const fetch = require("node-fetch");
const path = require("path");

// Get NR credentials from env
const accountId = process.env.E2E_NEWRELIC_ACCOUNTID;
const apiKey = process.env.E2E_NEWRELIC_INGEST_KEY;

// Our reporter implements only the onRunComplete lifecycle
// function, run after all tests have completed
class CustomReporter {
  async onRunComplete(_, aggregateResult) {
    const events = [];
    // Aggregate result has results for tests in each file
    aggregateResult.testResults.forEach((file) => {
      // Those have results per `it` or `test` block.
      file.testResults.forEach((res) => {
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
          errorMessage: res.failureMessages.join("|"),
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
        events.push(event);
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
