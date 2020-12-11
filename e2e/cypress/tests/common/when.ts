import { When } from "cypress-cucumber-preprocessor/steps";
import { fineos, portal } from "./actions";
import { CypressStepThis, Credentials } from "../../../src/types";

/**
 * Continous of prevous claim
 */
When("I return to my previous application", function () {
  cy.contains("a", "View your applications").click();
  cy.unstash("claimId").then((claimId) => {
    cy.get(`a[href="/applications/checklist/?claim_id=${claimId}"]`).click();
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

When("I log into the employer portal", function (this: CypressStepThis) {
  if (!this.credentials) {
    throw new Error("Unable to determine credentials");
  }
  portal.employerLogin(this.credentials);
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
When("I submit the employer registration form", function () {
  if (!this.credentials) {
    throw new Error("Credentials not properly set");
  }
  cy.contains("a", "Create an employer account").click();
  cy.labelled("Email address").type(this.credentials.username);
  cy.labelled("Password").type(this.credentials.password);
  cy.labelled("Employer ID number").type(this.credentials.fein);
  cy.stashLog("leaveAdminEmail", this.credentials.username);
  cy.stashLog("employerFEIN", this.credentials.fein);
  cy.contains("button", "Create account").click();
  cy.task("getAuthVerification", this.credentials.username as string).then(
    (code: string) => {
      cy.labelled("6-digit code").type(code as string);
      cy.contains("button", "Submit").click();
    }
  );
});
/* Account creation */
When("I submit the claimant registration form", function (
  this: CypressStepThis
) {
  if (!this.credentials) {
    throw new Error("Credentials not properly set");
  }

  portal.portalRegister(this.credentials);
});

When("I accept the terms of service", function () {
  // this action is forced because of trivial error: "this element is detached from the DOM"
  cy.contains("Agree and continue").click({ force: true });
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
  const { paymentPreference } = this;
  portal.submitClaimPortal(application, paymentPreference);
});

When("I see a pdf {string} notice to download", function (noticeType: string) {
  cy.unstash("claimNumber").then((id) => {
    cy.contains("article", id as string).within(() => {
      cy.get(".usa-list .text-medium").should("contain.text", noticeType);
      // @ToDo Will add later, currently just checking notice link
      //   .click();
      // cy.wait(15000);
    });
  });
});

When("I request additional information from the claimant", function (): void {
  fineos.onTab("Evidence");
  cy.get("input[type='submit'][value='Additional Information']").click();
  cy.get(
    "input[name*='healthcareProviderInformationIncompleteBoolean_CHECKBOX']"
  ).click();
  cy.get("input[name*='healthcareProviderInformationIncompleteText']").type(
    "Wrote Physician requesting revised page 1."
  );
  cy.get("textarea[name*='missingInformationBox']").type(
    "Please resubmit page 1 of the Healthcare Provider form to verify the claimant's demographic information.  The page provided is missing information.  Thank you."
  );
  fineos.clickBottomWidgetButton("OK");
});

When("I am the {string} claimant visiting the portal", function (
  loginType: string
): void {
  const credentials: Credentials = {
    username: Cypress.env("E2E_PORTAL_USERNAME"),
    password: Cypress.env("E2E_PORTAL_PASSWORD"),
  };
  if (loginType === "new") {
    cy.task("generateCredentials", false)
      .then((creds: Credentials) => {
        cy.stash("username", creds.username);
        cy.stash("password", creds.password);
        portal.portalRegister(creds as Credentials);
        portal.login(creds as Credentials);
        cy.contains("Agree and continue").click({ force: true });
      })
      .as("credentials");
  } else {
    portal.login(credentials);
  }
});
