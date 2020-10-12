import { Before } from "cypress-cucumber-preprocessor/steps";
// import "@rckeller/cypress-unfetch/await";

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
  cy.route({
    method: "POST",
    url:
      "https://paidleave-api-stage.mass.gov/api/v1/applications/*/submit_application",
  }).as("submitClaimResponse");
});

Before({ tags: "@fineos" }, () => {
  // Set up a route we can listen to wait on ajax rendering to complete.
  cy.route(/ajax\/pagerender\.jsp/).as("ajaxRender");
});
