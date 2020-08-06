export default class ConfirmPage {
  assertOnConfirm(): this {
    cy.url().should("include", "/claims/confirm");
    return this;
  }

  agreeAndSubmit(): this {
    this.assertOnConfirm();
    cy.contains("Agree and Submit My Application").click();
    cy.url({ timeout: 20000 }).should("include", "/claims/success");
    return this;
  }
}
