import { Then } from "cypress-cucumber-preprocessor/steps";
import { SuccessPage } from "@/pages";
import completeApplication from "./util";

Then("I should see a success page confirming my claim submission", function () {
  new SuccessPage().assertOnSuccess();
});

Then("I should be able to return to the portal dashboard", function () {
  new SuccessPage().returnToDashboard();
});

/**
 * Assert the data matches previously filled info
 */
Then("I should see any previously entered data", function (): void {
  cy.get('input[name="first_name"]').should(
    "have.value",
    this.application.firstName
  );
  cy.get('input[name="last_name"]').should(
    "have.value",
    this.application.lastName
  );
  cy.contains("button", "Continue").click();
  cy.get('input[name="date_of_birth_day"]').should(
    "have.value",
    this.application.dob.day.toString()
  );
  cy.get('input[name="date_of_birth_year"]').should(
    "have.value",
    this.application.dob.year.toString()
  );
  cy.contains("button", "Continue").click();
});

/**
 * Continue Submitting claim where fields are empty
 */
Then("I should be able to finish submitting the claim", function (): void {
  cy.contains("Do you have a Massachusetts driver's license or ID card?");
  if (this.application.massId) {
    cy.contains("Yes").click();
    cy.contains("Enter your license or ID number").type(
      this.application.massId
    );
  } else {
    cy.contains("No").click();
  }
  cy.contains("button", "Continue").click();

  if (
    !this.application.idVerification ||
    !this.application.idVerification.front ||
    !this.application.idVerification.back
  ) {
    throw new Error("Missing ID verification. Did you forget to generate it?");
  }

  cy.get('input[type="file"]')
    .attachFile(this.application.idVerification.front)
    .attachFile(this.application.idVerification.back);
  cy.contains("button", "Continue").click();

  cy.contains("What's your Social Security Number?").type(this.application.ssn);
  cy.contains("button", "Continue").click();

  completeApplication(this.application);
});

/**
 * Find claim in Fineos.
 *
 * @param claimId The Claim ID, as reported from the portal.
 */
Then("I should find their claim in Fineos", function () {
  // Fetch the claimId from the previous step, then use it in submission to Fineos.
  cy.unstash("claimId").then((claimId) => {
    if (typeof claimId !== "string") {
      throw new Error("Invalid Claim ID from previous test.");
    }
    cy.get(`[title="PFML API ${claimId}"]`).click();
    // For now, we're stopping at asserting that the claim made it to Fineos.
  });
});
