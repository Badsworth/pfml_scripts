import { Before } from "cypress-cucumber-preprocessor/steps";

Before({ tags: "@registerAccount" }, function () {
  // Get application.
  cy.fixture("registerAccount").then((application) => {
    cy.wrap(application).as("application");
  });
});
