import { When } from "cypress-cucumber-preprocessor/steps";
import { TestType } from "@/types";

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
    .contains("a", label === "Add payment information" ? "Resume" : "Start")
    .click();
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
      application.employee_ssn.split("-").join("")
    );
    cy.get('input[type="submit"][value="Search"]').click();
    cy.contains("table.WidgetPanel", "Person Search Results").within(() => {
      cy.contains(
        ".ListTable tr",
        `xxxxx${application.employee_ssn.slice(-4)}`
      ).click();
    });
    cy.contains('input[type="submit"]', "OK").click();
    cy.contains(".TabStrip td", "Cases").click({ force: true });
  });
});
