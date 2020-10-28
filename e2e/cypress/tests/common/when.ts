import { When } from "cypress-cucumber-preprocessor/steps";
import { fineos, portal } from "./actions";
import { CypressStepThis } from "@/types";

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

When("I log into the portal", function (this: CypressStepThis) {
  if (!this.credentials) {
    throw new Error("Unable to determine credentials");
  }
  cy.visit("/");
  portal.login(this.credentials);
});

When("I confirm that I am an eligible parent", function (): void {
  portal.confirmEligibleParent();
});

/* Checklist Page */
When("I click on the checklist button called {string}", function (
  label: string
): void {
  portal.clickChecklistButton(label);
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

/* Account creation */
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
  cy.task("getAuthVerification", this.credentials.username as string).then(
    (code: string) => {
      cy.labelled("6-digit code").type(code as string);
      cy.contains("button", "Submit").click();
    }
  );
});
When("I accept the terms of service", function () {
  cy.contains("Agree and continue").click();
});

When("I finish managing evidence", function () {
  fineos.clickBottomWidgetButton();
});

When("I have submitted all parts of the claim", function (
  this: CypressStepThis
): void {
  if (!this.application) {
    throw new Error("Can't find application");
  }
  const { application } = this;
  portal.submitClaimPortal(application);
});
