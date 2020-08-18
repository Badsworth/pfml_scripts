import { When } from "cypress-cucumber-preprocessor/steps";
import { LoginPage } from "@/pages";
import { TestType } from "@/types";
import completeApplication from "./util";

/**
 * Submits a claim.
 */
When("I submit the claim", function () {
  // Submit the remaining parts of the claim
  completeApplication(this.application);
});

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
When("I log out and log back into the portal", function () {
  cy.contains("button", "Log out").click();
  cy.url().should("contain", "/login");
  new LoginPage().login(this.application);
});

/**
 * Search on an applicant in Fineos.
 */
When("I search for the {testType} application in Fineos", function (
  testType: TestType
) {
  cy.fixture(testType).then((application) => {
    // @todo: We'll want to move this into page classes when we have more complex Fineos operations
    // to do. For now, it's just roughed in here.
    cy.visit("/");
    cy.get('a[aria-label="Parties"]').click();
    cy.labelled("Identification Number").type(
      application.ssn.split("-").join("")
    );
    cy.get('input[type="submit"][value="Search"]').click();
    cy.contains("table.WidgetPanel", "Person Search Results").within(() => {
      cy.contains(".ListTable tr", `xxxxx${application.ssn.slice(-4)}`).click();
    });
    cy.contains('input[type="submit"]', "OK").click();
    cy.contains(".TabStrip td", "Cases").click({ force: true });
  });
});
