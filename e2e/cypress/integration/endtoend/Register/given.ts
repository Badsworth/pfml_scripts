import { Given } from "cypress-cucumber-preprocessor/steps";

Given("I am an anonymous user on the portal homepage", () => {
  cy.visit("/");
  cy.task("generateCredentials").as("credentials");
});
