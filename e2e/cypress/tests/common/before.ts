import { Before } from "cypress-cucumber-preprocessor/steps";

Before({ tags: "@portal" }, () => {
  // Set the feature flag necessary to see the portal.
  cy.setCookie(
    "_ff",
    JSON.stringify({
      pfmlTerriyay: true,
    }),
    { log: true }
  );

  // Setup a route for application submission so we can extract claim ID later.
  cy.route2({
    method: "POST",
    url: "**/api/v1/applications/*/submit_application",
  }).as("submitClaimResponse");

  // Block new-relic.js outright due to issues with Cypress networking code.
  // Without this block, test retries on the portal error out due to fetch() errors.
  cy.route2("**/new-relic.js", (req) => {
    req.reply("console.log('Fake New Relic script loaded');");
  });
});

Before({ tags: "@fineos" }, () => {
  // Supress known application errors in Fineos.
  cy.on("uncaught:exception", (e) => {
    return !e.message.includes(`#.CaseOwnershipSummaryPanelElement`);
  });
  // Set up a route we can listen to wait on ajax rendering to complete.
  cy.route2(/ajax\/pagerender\.jsp/).as("ajaxRender");
});
