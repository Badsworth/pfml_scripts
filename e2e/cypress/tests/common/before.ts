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
});

Before({ tags: "@fineos" }, () => {
  // Set up a route we can listen to wait on ajax rendering to complete.
  cy.route2(/ajax\/pagerender\.jsp/).as("ajaxRender");
});
