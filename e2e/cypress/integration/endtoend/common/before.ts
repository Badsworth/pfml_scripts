import { Before } from "cypress-cucumber-preprocessor/steps";
import "@rckeller/cypress-unfetch/await";

Before({ tags: "@setFeatureFlags" }, () => {
  cy.setCookie(
    "_ff",
    JSON.stringify({
      pfmlTerriyay: true,
    })
  );
});

Before({ tags: "@catchStatusError" }, () => {
  cy.on("uncaught:exception", (e) => {
    // Suppress failures due to this error, which we can't do anything about.
    if (e.message.indexOf(`Cannot set property 'status' of undefined`)) {
      return false;
    }
  });
});

Before({ tags: "@routeRequest" }, () =>
  cy
    .route({
      method: "POST",
      url:
        "https://paidleave-api-stage.mass.gov/api/v1/applications/*/submit_application",
    })
    .as("submitClaimResponse")
);
