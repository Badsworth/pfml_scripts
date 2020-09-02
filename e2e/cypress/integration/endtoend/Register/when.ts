import { When } from "cypress-cucumber-preprocessor/steps";
import { CypressStepThis } from "@/types";

When("I submit the account registration form", function (
  this: CypressStepThis
) {
  if (!this.credentials) {
    throw new Error("Credentials not properly set");
  }
  cy.visit("/");
  cy.contains("a", "create an account").click();
  cy.labelled("Email address").type(this.credentials.username);
  cy.labelled("Password").type(this.credentials.password);
  cy.contains("button", "Create account").click();
});
