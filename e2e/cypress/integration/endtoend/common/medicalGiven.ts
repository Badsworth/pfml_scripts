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
  // cy.fixture(testType).wrap("application")
  cy.fixture(testType).then((application) => {
    cy.wrap(application).as("application");
  });
});

Given("I create an application", function (): void {
  cy.get('[href="/claims/start/"]').click();
});

Given("I start an application", function (): void {
  cy.contains("button", "I understand and agree").click();
});

Given("I have a claim ID", function (): void {
  cy.url()
    .should("include", "claim_id")
    .then((url) => {
      // Extract the Claim ID from the URL and stash it.
      const appId = new URL(url).searchParams.get("claim_id");
      if (appId) {
        cy.stash("claimId", appId);
      }
    });
});

// Usually followed by - "I have my identity verified"

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

/* Start Page */
Given("I am on the claims Start page", function (): void {
  cy.url().should("include", "/claims/start");
});
