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
    .contains("a", "Start")
    .click();
});

/**
 * Search on an applicant in Fineos.
 */
When("I search for the {testType} application in Fineos", function (
  testType: TestType
) {
  cy.fixture(testType).then(() => {
    cy.visit("/");
    cy.get('a[aria-label="Cases"]').click();
    cy.get('td[keytipnumber="4"]').contains("Case").click();

    /* For Testing (hard coded Claim Number)
      cy.labelled("Case Number").type("NTN-84-ABS-01");
    */
    cy.unstash("ClaimNumber").then((claimNumber) => {
      cy.labelled("Case Number").type(claimNumber as string);
    });
    cy.get('input[type="submit"][value="Search"]').click();
  });
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
  cy.get('td[class="secondMenu"]').contains("Deny").click();
});

When("I click Add", function () {
  cy.get("input[type='submit'][title='Add a task to this case']").click({
    force: true,
    timeout: 30000,
  });
});

When("I select Ineligible for Denial Reason", function (): void {
  cy.get('span[id="leaveRequestDenialDetailsWidget"]')
    .find("select")
    .select("Ineligible");
});

When("I search for Evidence Review", function (): void {
  cy.get("#NameSearchWidget")
    .find('input[type="text"]')
    .type("Evidence Review");
  cy.get("#NameSearchWidget").find('input[type="submit"]').click();
});

When("I click Open", function (): void {
  cy.get("input[type='submit'][title='Open this task']").click();
});
