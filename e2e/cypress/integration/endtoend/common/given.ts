import { Given } from "cypress-cucumber-preprocessor/steps";
import { portal, fineos } from "./actions";

Given("I am an anonymous user on the portal homepage", () => {
  cy.visit("/");
  cy.task("generateCredentials").as("credentials");
});

Given("I begin the process to submit a {string} claim", function (
  scenario: string
) {
  this.credentials = {
    username: Cypress.env("E2E_PORTAL_USERNAME"),
    password: Cypress.env("E2E_PORTAL_PASSWORD"),
  };
  portal.submittingClaimType(scenario);
  portal.login(this.credentials);
  portal.startClaim();
  portal.onPage("start");
  portal.agreeToStart();
  portal.hasClaimId();
  portal.onPage("checklist");
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

Given("I submit {string} claim directly to API", function (
  scenario: string
): void {
  // Needs to be on fineos base url
  // before submitting the claim
  // because when we change the base url
  // the whole test restarts
  fineos.loginSavilinx();
  cy.visit("/");
  portal.submitClaimDirectlyToAPI(scenario);
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

Given("the document {string} has been uploaded", function (
  label: string
): void {
  fineos.uploadDocument(label);
});
