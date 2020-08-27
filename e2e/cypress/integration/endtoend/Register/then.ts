import { Then } from "cypress-cucumber-preprocessor/steps";

Then("I should be able to register a new account", function () {
  cy.task("getAuthVerification", this.application.email as string).then(
    (code: string) => {
      cy.labelled("6-digit code").type(code as string);
      cy.contains("button", "Submit").click();
    }
  );
});
