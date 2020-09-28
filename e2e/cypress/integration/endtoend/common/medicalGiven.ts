import { Given } from "cypress-cucumber-preprocessor/steps";
import { getFineosBaseUrl } from "@/index";
import { CypressStepThis, TestType } from "@/types";

Given("I am logged in as a Savilinx CSR on the Fineos homepage", function () {
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
  cy.url().should("include", "claim_id");
});

// Usually followed by - "I have my identity verified"

Given("I am on the claims {string} page", function (pageName: string): void {
  cy.url({ timeout: 20000 }).should("include", `/claims/${pageName}`);
});

/* Fineos Claim Case Page */
Given("I am on the claim case page", function (): void {
  cy.url().should(
    "include",
    "/sharedpages/casemanager/displaycase/displaycasepage"
  );
});

/* Fineos Transfer to Dept Page */
Given("I am on the Transfer to Dept page", function (): void {
  cy.url().should("include", "/sharedpages/workmanager/transfertodeptpage");
});

Given("claim is financially ineligible", function (): void {
  cy.get('td[title="Not Met"]');
});

Given("claim is rejected", function (): void {
  cy.get('td[title="Rejected"]');
});

/* Fineos Claim Case Page */
Given("I am on the claim case page", function (): void {
  cy.url().should(
    "include",
    "/sharedpages/casemanager/displaycase/displaycasepage"
  );
});

/* Paid Benefits Tab */
Given("I am on the tab {string}", function (label: string): void {
  cy.get('td[class="TabOff"]').contains(label).click().wait(2000);
});
