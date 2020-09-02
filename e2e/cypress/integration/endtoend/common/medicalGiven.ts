import { Given } from "cypress-cucumber-preprocessor/steps";
import { getFineosBaseUrl } from "@/index";
import { CypressStepThis, TestType } from "@/types";

Given("I am logged in as a CSR on the Fineos homepage", function () {
  Cypress.config("baseUrl", getFineosBaseUrl());
});

Given("I log in as a claimant on the portal dashboard", function () {
  const credentials: CypressStepThis["credentials"] = {
    username: Cypress.env("PORTAL_USERNAME"),
    password: Cypress.env("PORTAL_PASSWORD"),
  };
  // Alias the credentials for later use.
  cy.wrap(credentials).as("credentials");
  cy.visit("/");
  cy.labelled("Email address").type(credentials.username);
  cy.labelled("Password").typeMasked(credentials.password);
  cy.contains("button", "Log in").click();
});

Given("I have a {testType} claim to submit", function (testType: TestType) {
  // Get application.
  cy.fixture(testType).wrap("application");
});

Given("I create an application", function (): void {
  cy.contains("button", "Create an application").click();
  cy.url()
    .should("include", "claim_id")
    .then((url) => {
      // Extract the Claim ID from the URL and stash it.
      const appId = new URL(url).searchParams.get("claim_id");
      if (appId) {
        cy.stash("claimId", appId);
      }
    });
  // Usually followed by - "I have my identity verified"
});

/* Confirm Page */
Given("I am on the claims Confirm page", function (): void {
  cy.url().should("include", "/claims/confirm");
});

/* Review Page */
Given("I am on the claims Review page", function (): void {
  cy.url().should("include", "/claims/review");
});

/* Checklist Page */
Given("I am on the claims Checklist page", function (): void {
  cy.url().should("include", "/claims/checklist");
});

/* Checklist Page */
Given("I click on the checklist button called {string}", function (
  label: string
): void {
  // @todo: Very brittle selector. Ask for a better one.
  cy.contains(label)
    .parentsUntil(".display-flex.border-bottom.border-base-light.padding-y-4")
    .contains("a", "Start")
    .click();
});

Given("I have my identity verified", function (this: CypressStepThis): void {
  if (!this.application) {
    throw new Error("Application has not been set");
  }
  const { application } = this;
  // Preceeded by - "I am on the claims Checklist page";
  // Preceeded by - "I click on the checklist button called {string}"
  //                with the label "Verify your identity"
  if (
    !application.idVerification ||
    !application.idVerification.front ||
    !application.idVerification.back
  ) {
    throw new Error("Missing ID verification. Did you forget to generate it?");
  }

  cy.labelled("First name").type(application.firstName);
  cy.labelled("Last name").type(application.lastName);
  cy.contains("button", "Continue").click();

  cy.contains("fieldset", "What's your birthdate?").within(() => {
    cy.contains("Month").type(application.dob.month.toString());
    cy.contains("Day").type(application.dob.day.toString());
    cy.contains("Year").type(application.dob.year.toString());
  });
  cy.contains("button", "Continue").click();

  cy.contains("Do you have a Massachusetts driver's license or ID card?");
  if (application.massId) {
    cy.contains("Yes").click();
    cy.contains("Enter your license or ID number").type(application.massId);
  } else {
    cy.contains("No").click();
  }
  cy.contains("button", "Continue").click();

  cy.contains("What's your Social Security Number?").type(application.ssn);
  cy.contains("button", "Continue").click();

  // Input was removed from portal at some point
  // If it reappears, generate the PDF here and upload.
  // cy.get('input[type="file"]')
  //  .attachFile(application.idVerification.front)
  //  .attachFile(application.idVerification.back);
  // cy.contains("button", "Continue").click();
});
