import { Before } from "cypress-cucumber-preprocessor/steps";

export function beforePortal(): void {
  // Set the feature flag necessary to see the portal.
  cy.setCookie(
    "_ff",
    JSON.stringify({
      pfmlTerriyay: true,
      claimantShowAuth: true,
      claimantShowMedicalLeaveType: true,
    }),
    { log: true }
  );

  cy.on("uncaught:exception", (e) => {
    if (e.message.match(/Cannot set property 'status' of undefined/)) {
      return false;
    }
    return true;
  });

  // Setup a route for application submission so we can extract claim ID later.
  cy.intercept({
    method: "POST",
    url: "**/api/v1/applications/*/submit_application",
  }).as("submitClaimResponse");

  cy.intercept({
    method: "GET",
    url: "**/api/v1/applications/*/documents",
  }).as("documentClaimResponse");

  // Block new-relic.js outright due to issues with Cypress networking code.
  // Without this block, test retries on the portal error out due to fetch() errors.
  cy.intercept("**/new-relic.js", (req) => {
    req.reply("console.log('Fake New Relic script loaded');");
  });
}

export function beforeFineos(): void {
  // Supress known application errors in Fineos.
  cy.on("uncaught:exception", (e) => {
    if (
      e.message.match(
        /#.(CaseOwnershipSummaryPanelElement|CaseParticipantsSummaryPanelElement)/
      )
    ) {
      return false;
    }
    if (e.message.match(/Cannot set property 'status' of undefined/)) {
      return false;
    }
    return true;
  });
  // Block new-relic.js outright due to issues with Cypress networking code.
  // Without this block, test retries on the portal error out due to fetch() errors.
  cy.intercept("*js-agent.newrelic.com/*", (req) => {
    req.reply("console.log('Fake New Relic script loaded');");
  });
  // cy.intercept("**/new-relic.js", (req) => {
  //   req.reply("console.log('Fake New Relic script loaded');");
  // });

  // Set up a route we can listen to wait on ajax rendering to complete.
  cy.intercept(/ajax\/pagerender\.jsp/).as("ajaxRender");
}

Before({ tags: "@portal" }, beforePortal);
Before({ tags: "@fineos" }, beforeFineos);
