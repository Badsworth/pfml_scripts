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
