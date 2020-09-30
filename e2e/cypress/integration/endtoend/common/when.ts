import { When } from "cypress-cucumber-preprocessor/steps";
import { fineos } from "./actions";

/**
 * Continous of prevous claim
 */
When("I return to my previous application", function () {
  cy.contains("a", "View your applications").click();
  cy.unstash("claimId").then((claimId) => {
    cy.get(`a[href="/claims/checklist/?claim_id=${claimId}"]`).click();
  });
  cy.contains("a", "Resume").click();
});

/**
 * Logout/Login
 */
When("I log out", function () {
  cy.contains("button", "Log out").click();
  cy.url().should("contain", "/login");
});

/* Checklist Page */
When("I click on the checklist button called {string}", function (
  label: string
): void {
  // @todo: Very brittle selector. Ask for a better one.
  cy.contains(label)
    .parentsUntil(".display-flex.border-bottom.border-base-light.padding-y-4")
    .contains("a", "Start")
    .click();
});

/* Checklist Page */
When("I resume {string}", function (label: string): void {
  // @todo: Very brittle selector. Ask for a better one.
  cy.contains(label)
    .parentsUntil(".display-flex.border-bottom.border-base-light.padding-y-4")
    .contains("a", "Resume")
    .click();
});

When("I click Adjudicate", function () {
  cy.get('input[type="submit"][value="Adjudicate"]').click();
});

When("I click edit", function () {
  cy.wait(2000).get('input[type="submit"][value="Edit"]').click();
});

When("I click Manage Evidence", function (): void {
  cy.wait(2000).get('input[type="submit"][value="Manage Evidence"]').click();
});

When("I highlight ID Proof", function (): void {
  cy.wait(2000).get('.ListRow2 > [width="20%"]').click();
});

When("I click Deny", function () {
  fineos.clickDeny();
});

When("I complete adding Evidence Review Task", function (): void {
  fineos.addEvidenceReviewTask();
});

When("I select {string} for Denial Reason", function (reason: string): void {
  cy.get('span[id="leaveRequestDenialDetailsWidget"]')
    .find("select")
    .select(reason);
});
