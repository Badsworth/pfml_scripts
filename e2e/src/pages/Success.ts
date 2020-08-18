export default class SuccessPage {
  assertOnSuccess(): this {
    cy.url().should("include", "/claims/success");
    return this;
  }

  returnToDashboard(): this {
    cy.contains("Return to dashboard").click();
    cy.url().should("equal", `${Cypress.config().baseUrl}/`);
    return this;
  }
}
