import { Given, Then, When } from "cypress-cucumber-preprocessor/steps";
import { fineos } from "./actions";

Given("I am logged into Fineos as a Savilinx user", () => {
  fineos.loginSavilinx();
});

// Initial step to view a just-submitted Portal claim.
Then("I should be able to find claim in Adjudication", () => {
  cy.unstash("claimNumber").as("claimNumber");
  cy.get<string>("@claimNumber").then(fineos.visitClaim);

  // For Testing
  // fineos.visitClaim("NTN-4368-ABS-01")
});

Then("I should be able to find employer page", () => {
  cy.unstash("employerFEIN").then((employerFEIN) => {
    if (typeof employerFEIN !== "string") {
      throw new Error("FEIN must be a string");
    }
    fineos.visitEmployer(employerFEIN);
  });
});

Then("I should be able to find the POC", () => {
  cy.unstash("leaveAdminEmail").then((leaveAdminEmail) => {
    if (typeof leaveAdminEmail !== "string") {
      throw new Error("Email must be a string");
    }
    fineos.confirmPOC(leaveAdminEmail);
  });
});

// Initial step to use a previously submitted claim by ID.
Given("I am viewing claim {string}", (claimId: string) => {
  cy.wrap(claimId).as("claimNumber");
  fineos.visitClaim(claimId);
});

When("I start adjudication for the claim", () => {
  cy.unstash<string>("claimNumber").then((claimNumber) => {
    fineos.assertOnClaimPage(claimNumber);
  });
  cy.get("input[type='submit'][value='Adjudicate']").click();
});

When("I add paid benefits to the current case", () => {
  cy.get<string>("@claimNumber").then(fineos.assertAdjudicatingClaim);
  fineos.onTab("Paid Benefits");
  cy.get("input[type='submit'][value='Edit']").click();
  cy.labelled("Average weekly wage").type("{selectall}{backspace}1000");
  cy.contains(
    "div[class='flex-item']",
    "Benefit payment waiting period"
  ).within(() => {
    cy.get("input").first().type("{selectall}{backspace}10");
    cy.get("select").select("Days");
  });
  fineos.clickBottomWidgetButton("OK");
});

When(
  "I mark {string} {string} documentation as satisfactory",
  (claimType: string, evidenceType: string) => {
    cy.get<string>("@claimNumber").then(fineos.assertAdjudicatingClaim);
    fineos.onTab("Evidence");
    cy.contains(".ListTable td", evidenceType).click();
    cy.get("input[type='submit'][value='Manage Evidence']").click();
    // Focus inside popup.
    cy.get(".WidgetPanel_PopupWidget").within(() => {
      if (claimType === "BGBM1") {
        cy.labelled("Evidence Receipt").select("Received");
      }
      cy.labelled("Evidence Decision").select("Satisfied");
      cy.labelled("Evidence Decision Reason").type(
        "{selectall}{backspace}Evidence has been reviewed and approved"
      );
      cy.get("input[type='button'][value='OK']").click();
      // Wait till modal has fully closed before moving on.
      cy.get("#disablingLayer").should("not.exist");
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

Then("I can commence intake on that claim", () => {
  cy.unstash("claimNumber").as("claimNumber");
  cy.get<string>("@claimNumber").then(fineos.commenceIntake);
});

Then("I should confirm proper tasks have been created", function (): void {
  fineos.onTab("Task");
  cy.get(`.divListviewGrid .ListTable td[title='Certification Review']`).should(
    "have.text",
    "Certification Review"
  );
  cy.get(`.divListviewGrid .ListTable td[title='ID Review']`).should(
    "have.text",
    "ID Review"
  );
  fineos.onTab("Absence Hub");
});

Then("I confirm proper RMV ID status as {string}", function (
  RMVStatus: string
): void {
  let statusText = "";
  switch (RMVStatus) {
    case "valid":
      statusText = "Verification check passed";
      cy.get("div[id*='identificationStatus']").should(
        "contain.text",
        statusText
      );
      break;

    case "invalid":
    case "fraud":
      statusText =
        "Verification failed because no record could be found for given ID information";
      cy.get("div[id*='identificationStatus']").should(
        "contain.text",
        statusText
      );
      break;

    case "mismatch":
      statusText = "Verification failed because ID number mismatch";
      cy.get("div[id*='identificationStatus']").should(
        "contain.text",
        statusText
      );
      break;

    default:
      throw new Error("RMV Status Type not found!");
  }
});
