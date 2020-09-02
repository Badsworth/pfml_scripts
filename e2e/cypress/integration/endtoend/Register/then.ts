import { Then } from "cypress-cucumber-preprocessor/steps";
import { CypressStepThis } from "@/types";

Then("I should be able to register a new account", function (
  this: CypressStepThis
) {
  if (!this.credentials) {
    throw new Error("Credentials not properly set");
  }
  cy.task("getAuthVerification", this.credentials.username as string).then(
    (code: string) => {
      cy.labelled("6-digit code").type(code as string);
      cy.contains("button", "Submit").click();
    }
  );
});

Then("I should be able to log in", function (this: CypressStepThis) {
  if (!this.credentials) {
    throw new Error("Credentials not properly set");
  }
  cy.labelled("Email address").type(this.credentials.username);
  cy.labelled("Password").typeMasked(this.credentials.password);
  cy.contains("button", "Log in").click();
  cy.contains("button", "Log out").should("be.visible");
});
