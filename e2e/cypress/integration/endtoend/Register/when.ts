import { When } from "cypress-cucumber-preprocessor/steps";

When("I submit the account registration form", function () {
  cy.visit("/");
  cy.contains("a", "create an account").click();
  cy.labelled("Email address").type(this.application.email);
  cy.labelled("Password").type(this.application.password);
  cy.contains("button", "Create account").click();
});
