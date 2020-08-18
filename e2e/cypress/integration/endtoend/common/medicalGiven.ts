import { Given } from "cypress-cucumber-preprocessor/steps";
import { getFineosBaseUrl } from "@/index";
import { LoginPage, ChecklistPage } from "@/pages";
import { TestType } from "@/types";

Given("I am logged in as a CSR on the Fineos homepage", function () {
  Cypress.config("baseUrl", getFineosBaseUrl());
});

Given("I am logged in as a claimant on the portal dashboard", function () {
  new LoginPage().login(this.application);
});

Given("I have a {testType} claim to submit", function (testType: TestType) {
  // Get application.
  cy.fixture(testType).then((application) => {
    application.email = Cypress.env("PORTAL_USERNAME");
    application.password = Cypress.env("PORTAL_PASSWORD");
    cy.generateIdVerification(application).then((applicationWithIdentity) => {
      cy.generateHCPForm(applicationWithIdentity).then((application) => {
        cy.wrap(application).as("application");
      });
    });
  });
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
  new ChecklistPage().verifyIdentity(this.application);
});
