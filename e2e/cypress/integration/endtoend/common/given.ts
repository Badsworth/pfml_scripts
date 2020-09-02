import { Given } from "cypress-cucumber-preprocessor/steps";

// todo: dynamic url for homepage
Given("I am an anonymous user on the portal homepage", () => {
  cy.visit("/");
});
