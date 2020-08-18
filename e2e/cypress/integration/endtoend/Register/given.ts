import { Given } from "cypress-cucumber-preprocessor/steps";

Given("I have an application to submit", function () {
  // Get application.
  cy.fixture("registerAccount").then((application) => {
    cy.wrap(application).as("application");
  });
});
