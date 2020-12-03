import { CypressStepThis } from "../../../src/types";
import { Given } from "cypress-cucumber-preprocessor/steps";
import { portal, fineos } from "./actions";

Given("I am an anonymous user on the portal homepage", () => {
  cy.visit("/");
  cy.task("generateCredentials", false).as("credentials");
});

Given("I am an anonymous employer user on the portal homepage", () => {
  cy.visit("/");
  cy.task("generateCredentials", true).as("credentials");
});

Given("I begin to submit a {string} claim as a {string} employee", function (
  scenario: string,
  employeeType: string
) {
  const credentials = {
    username: Cypress.env("E2E_PORTAL_USERNAME"),
    password: Cypress.env("E2E_PORTAL_PASSWORD"),
  };
  portal.startSubmit(credentials, scenario, employeeType);
});

Given("I search for the proper claim in Fineos", function () {
  fineos.loginSavilinx();
  fineos.searchScenario();
  fineos.findClaim();
  fineos.onPage("claims");
});

Given("I am on the claims {string} page", function (page: string) {
  portal.onPage(page);
});

/* Fineos Claim Case Page */
Given("I am on the claim case page", function () {
  fineos.onPage("claims");
});

Given(
  "I submit a {string} claim directly to API as a {string} employee",
  function (scenario: string, employeeType: string): void {
    portal.submitClaimDirectlyToAPI(scenario, employeeType);
  }
);

Given("Part One of the claim has been submitted", function (
  this: CypressStepThis
): void {
  if (!this.application) {
    throw new Error("Can't find application");
  }
  const { application } = this;
  portal.submitClaimPartOne(application);
});

Given("I complete claim Denial for {string}", function (reason: string): void {
  fineos.denialReason(reason);
});

Given("I start an application", function (): void {
  cy.contains("button", "I understand and agree").click();
});

Given("I have a claim ID", function (): void {
  cy.url().should("include", "claim_id");
});

Given("claim is financially ineligible", function (): void {
  cy.get('td[title="Not Met"]');
});

Given("claim is rejected", function (): void {
  cy.get('td[title="Rejected"]');
});

/* Paid Benefits Tab */
Given("I am on the tab {string}", function (label: string): void {
  cy.get('td[class="TabOff"]').contains(label).click().wait(2000);
});

Given(
  "the document {string} has been uploaded with {string} business type",
  function (label: string, type: string): void {
    fineos.uploadDocument(label, type);
  }
);

Given("I click through the commence intake flow", function (): void {
  cy.get("#nextPreviousButtons").contains("Next").click();
  cy.get("#nextPreviousButtons").contains("Next").click();
  cy.get("#nextPreviousButtons").contains("Next").click();
});

Given("I am on the page for that claim", function (): void {
  portal.viewClaim();
});

Given("I go directly to the ID upload page", function (): void {
  portal.goToIdUploadPage();
});

Given("I have added payment information", function (
  this: CypressStepThis
): void {
  if (!this.application) {
    throw new Error("Application has not been set");
  }
  // const { application } = this;
  portal.onPage("checklist");
  portal.clickChecklistButton("Add payment information");
  // portal.addPaymentInfo(application);
});

Given("I return to the portal", function () {
  const portalBaseUrl = Cypress.env("E2E_PORTAL_BASEURL");
  if (!portalBaseUrl) {
    throw new Error("Portal base URL must be set");
  }
  Cypress.config("baseUrl", portalBaseUrl);
  const credentials = {
    username: Cypress.env("E2E_PORTAL_USERNAME"),
    password: Cypress.env("E2E_PORTAL_PASSWORD"),
  };
  portal.login(credentials);
});
