// eslint-disable-next-line @typescript-eslint/no-var-requires
const fetch = require("node-fetch");

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
          runId: process.env.GITHUB_RUN_ID,
          environment: process.env.E2E_ENVIRONMENT,
          eventType: "IntergrationTestResult",
          filename: file.testFilePath.split("e2e/")[1],
          specStart: file.perfStats.start,
          specEnd: file.perfStats.end,
          specRuntime: file.perfStats.runtime,
          status: res.status,
          fullName: res.fullName,
          duration: res.duration,
          title: res.title,
          errorMessage: res.failureMessages.join("|"),
        };
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
