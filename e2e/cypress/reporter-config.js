/**
 * This file sets up our reporters.
 *
 * In local environments, we just use the `spec` reporter. In CI,
 * we also use the custom New Relic reporter.
 *
 * This code is JS because it's required directly by Cypress, not transpiled.
 */
/* eslint-disable @typescript-eslint/no-var-requires */
require("dotenv").config();
const { Parser } = require("yargs/helpers");

const config = {
  reporterEnabled: "spec",
};

// Parse the Cypress input to determine group, ci-build-id, etc. This is
// pretty dirty, but there's no other way to get at this information.
// Strip off the -- argument, which prevents us from parsing further args.
const args = Parser(process.argv.filter((a) => a !== "--"));

const runId = args.ciBuildId ?? process.env.E2E_RUNID;

if (runId) {
  const { E2E_NEWRELIC_ACCOUNTID, E2E_NEWRELIC_INGEST_KEY, E2E_ENVIRONMENT } =
    process.env;
  config.reporterEnabled += ",cypress/reporters/new-relic.js";
  config.cypressReportersNewRelicJsReporterOptions = {
    accountId: E2E_NEWRELIC_ACCOUNTID ?? "2837112",
    apiKey: E2E_NEWRELIC_INGEST_KEY,
    runId,
    environment: E2E_ENVIRONMENT,
    group: args.group,
    tag: args.tag,
  };
}

module.exports = config;
