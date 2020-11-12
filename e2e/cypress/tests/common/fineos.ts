import { Given, Then, When } from "cypress-cucumber-preprocessor/steps";
import { fineos } from "./actions";
import { formatDateString } from "./util";

Given("I am logged into Fineos as a Savilinx user", () => {
  fineos.loginSavilinx();
});

// Initial step to view a just-submitted Portal claim.
Then("I should be able to find claim in Adjudication", () => {
  cy.unstash("claimNumber").as("claimNumber");
  cy.get<string>("@claimNumber").then(fineos.visitClaim);
});

// Initial step to use a previously submitted claim by ID.
Given("I am viewing claim {string}", (claimId: string) => {
  cy.wrap(claimId).as("claimNumber");
  fineos.visitClaim(claimId);
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
  cy.contains(
    "div[class='flex-item']",
    "Benefit payment waiting period"
  ).within(() => {
    cy.get("input").first().type("10");
    cy.get("select").select("Days");
  });
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

Then("I can commence intake on that claim", () => {
  cy.unstash("claimNumber").as("claimNumber");
  cy.get<string>("@claimNumber").then(fineos.commenceIntake);
});

Given(
  "I find an employee in the FINEOS system",
  (claimType = "BHAP1", employeeType = "financially eligible") => {
    cy.task("generateClaim", {
      claimType: claimType,
      employeeType: employeeType,
    }).then((claim?: SimulationClaim) => {
      if (!claim) {
        throw new Error("Claim Was Not Generated");
      }
      cy.log("generated claim", claim.claim);
      cy.stashLog("firstName", claim.claim.first_name);
      cy.stashLog("lastName", claim.claim.last_name);
    });
  }
);

Then(
  "I begin to submit a new claim on that employee in FINEOS",
  function (): void {
    fineos.loginSavilinx();
    fineos.searchClaimant();
    fineos.clickBottomWidgetButton("OK");
    fineos.assertOnClaimantPage();
  }
);

Then("I start create a new notification", function (): void {
  cy.contains("span", "Create Notification").click();
  cy.get("span[id='nextContainer']").first().find("input").click();
  cy.get("span[id='nextContainer']").first().find("input").click();
  cy.contains(
    "div",
    "Bonding with a new child (adoption/ foster care/ newborn)"
  )
    .prev()
    .find("input")
    .click();
  cy.get("span[id='nextContainer']").first().find("input").click();
  cy.labelled("Qualifier 1").select("Foster Care");
  cy.get("span[id='nextContainer']")
    .first()
    .find("input")
    .click()
    .wait("@ajaxRender");
  cy.contains("div", "One or more fixed time off periods")
    .prev()
    .find("input[type='checkbox'][id*='continuousTimeToggle_CHECKBOX']")
    .click({ force: true });
  cy.get("span[id='nextContainer']").first().find("input").click();
  cy.labelled("Absence status").select("Estimated");
  cy.task("createContinuousLeaveDates").then((leaveDates?: Date[]) => {
    if (!leaveDates) {
      throw new Error("Leave dates are not defined.");
    }
    const [startdate, endDate] = leaveDates.map((date) =>
      formatDateString(date)
    );
    cy.labelled("Absence start date").type(`${startdate}{enter}`);
    cy.labelled("Absence end date").type(`${endDate}{enter}`, { force: true });
    cy.get(
      "input[type='button'][id*='AddTimeOffAbsencePeriod'][value='Add']"
    ).click();
    cy.wait("@ajaxRender");
    cy.wait(200);
    cy.wait("@ajaxRender");
    cy.get("span[id='nextContainer']")
      .first()
      .find("input")
      .click()
      .wait("@ajaxRender");
    cy.get("span[id='nextContainer']")
      .first()
      .find("input")
      .click()
      .wait("@ajaxRender");
    cy.get("span[id='nextContainer']")
      .first()
      .find("input")
      .click()
      .wait("@ajaxRender");
    cy.contains("div", "Thank you. Your notification has been submitted.");
  });
});
