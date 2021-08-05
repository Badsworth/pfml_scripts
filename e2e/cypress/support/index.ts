// ***********************************************************
// This example support/index.js is processed and
// loaded automatically before your test files.
//
// This is a great place to put global configuration and
// behavior that modifies Cypress.
//
// You can change the location of this file or turn off
// automatically serving support files with the
// 'supportFile' configuration option.
//
// You can read more here:
// https://on.cypress.io/configuration
// ***********************************************************

// Import commands.js using ES2015 syntax:
// eslint-disable-next-line @typescript-eslint/no-var-requires
require("cypress-grep")();
import "./commands";
import "./dependents";
import "cypress-file-upload";

Cypress.Keyboard.defaults({
  keystrokeDelay: 0,
});

// This will handle any Fineos or portal errors which are not caught by the applications themselves.
// It helps prevent unhandled rejections from spilling into neighboring specs.
Cypress.on("uncaught:exception", (err) => {
  // Handles fineos errors.
  if (
    err.message.match(
      /(#.(CaseOwnershipSummaryPanelElement|CaseParticipantsSummaryPanelElement)|panelsdrilldown|startHeartbeatMonitorForPage)/
    )
  )
    return false;
  // Those errors are encountered both in fineos and in portal
  if (
    err.message.match(
      /Cannot (set|read) property ('status'|'range') of undefined/
    )
  )
    return false;

  return true;
});

beforeEach(() => {
  // New Relic does not play well with Cypress, and results in a ton of errors
  // being logged to New Relic. Globally block the New Relic JS script in all tests.
  // Follow these issues for more info:
  // * https://discuss.newrelic.com/t/playing-better-with-cypress/120046
  // * https://github.com/cypress-io/cypress/issues/9058
  cy.intercept(/new-?relic.*\.js/, (req) => {
    req.reply("console.log('Fake New Relic script loaded');");
  });
});
