import { Given, Then, When } from "cypress-cucumber-preprocessor/steps";
import { fineos } from "@cypress/tests/common/actions";

Given("I am logged into Fineos as a Savilinx user", () => {
  fineos.loginSavilinx();
});

// Initial step to view a just-submitted Portal claim.
Given("I am viewing the previously submitted claim", () => {
  cy.unstash("claimNumber").as("claimNumber");
  cy.get<string>("@claimNumber").then(fineos.visitClaim);
});

// Initial step to use a previously submitted claim by ID.
Given("I am viewing claim {string}", (claimId: string) => {
  cy.wrap(claimId).as("claimNumber");
  fineos.visitClaim(claimId);
});

// Initial step to view a brand new claim submitted now by API:
Given("I am viewing a {string} claim", (scenario) => {
  // Submit claim first:
  cy.fixture(scenario).then({ timeout: 40000 }, (app) => {
    cy.task("submitClaimToAPI", app).as("claimNumber");
  });
  // Navigate to claim in UI.
  cy.get<string>("@claimNumber").then(fineos.visitClaim);
});

When("I start adjudication for the claim", () => {
  fineos.assertOnClaimPage();
  cy.get("input[type='submit'][value='Adjudicate']").click();
});

When("I add paid benefits to the current case", () => {
  cy.get<string>("@claimNumber").then(fineos.assertAdjudicatingClaim);
  fineos.onTab("Paid Benefits");
  cy.get("input[type='submit'][value='Edit']").click();
  cy.labelled("Average weekly wage").type("{selectall}{backspace}1000");
  fineos.clickBottomWidgetButton("OK");
});

When(
  "I mark {string} documentation as satisfactory",
  (evidenceType: string) => {
    cy.get<string>("@claimNumber").then(fineos.assertAdjudicatingClaim);
    fineos.onTab("Evidence");
    cy.contains(".ListTable td", evidenceType).click();
    cy.get("input[type='submit'][value='Manage Evidence']").click();
    // Focus inside popup.
    cy.get(".WidgetPanel_PopupWidget").within(() => {
      cy.labelled("Evidence Receipt").select("Received");
      cy.labelled("Evidence Decision").select("Satisfied");
      cy.labelled("Evidence Decision Reason").type(
        "{selectall}{backspace}Evidence has been reviewed and approved"
      );
      cy.get("input[type='button'][value='OK']").click();
      // Wait till modal has fully closed before moving on.
      cy.get("#disablingLayer").should("not.be.visible");
    });
  }
);

When("I fill in the requested absence periods", () => {
  cy.get<string>("@claimNumber").then(fineos.assertAdjudicatingClaim);
  fineos.onTab("Evidence");
  fineos.onTab("Certification Periods");
  cy.get("input[value='Prefill with Requested Absence Periods']").click();
  cy.get("#PopupContainer").within(() => {
    cy.get("input[value='Yes']").click();
  });
});

When("I finish adjudication for the claim", () => {
  cy.get<string>("@claimNumber").then(fineos.assertAdjudicatingClaim);
  fineos.clickBottomWidgetButton("OK");
});

Then(
  "I should see that the claim's {string} is {string}",
  (type: string, status: string) => {
    cy.get<string>("@claimNumber").then(fineos.assertAdjudicatingClaim);
    fineos.onTab("Manage Request");
    cy.get(".divListviewGrid .ListTable tr").should("have.length", 1);
    cy.get(
      `.divListviewGrid .ListTable td[id*='ListviewWidget${type}Status0']`
    ).should("have.text", status);
  }
);

Then("I should be able to approve the claim", () => {
  fineos.assertClaimApprovable();
});
