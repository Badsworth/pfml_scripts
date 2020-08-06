export default class ReviewPage {
  assertOnReview(): this {
    cy.url().should("include", "/claims/review");
    return this;
  }

  confirmInfo(): this {
    this.assertOnReview();
    cy.contains("Confirm information is correct").click();
    return this;
  }
}
