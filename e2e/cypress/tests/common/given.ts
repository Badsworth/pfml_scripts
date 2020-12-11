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
  portal.submittingClaimType(scenario, employeeType);
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
  cy.stashLog("employerFEIN", application.employer_fein);
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
  if (!this.paymentPreference) {
    throw new Error("Payment Preferences has not been set");
  }
  const { paymentPreference } = this;
  portal.onPage("checklist");
  portal.clickChecklistButton("Add payment information");
  portal.addPaymentInfo(paymentPreference);
});

Given("I return to the portal as the {string} claimant", function (
  loginType: string
) {
  const portalBaseUrl = Cypress.env("E2E_PORTAL_BASEURL");
  if (!portalBaseUrl) {
    throw new Error("Portal base URL must be set");
  }
  Cypress.config("baseUrl", portalBaseUrl);
  const credentials = {
    username: Cypress.env("E2E_PORTAL_USERNAME"),
    password: Cypress.env("E2E_PORTAL_PASSWORD"),
  };
  if (loginType === "new") {
    cy.unstash("username").as("username");
    cy.unstash("password").as("password");
    cy.visit("/login");
    cy.get<string>("@username").then((username) =>
      cy.labelled("Email address").type(username)
    );
    cy.get<string>("@password").then((password) =>
      cy.labelled("Password").typeMasked(password)
    );
    cy.contains("button", "Log in").click();
    cy.url().should("not.include", "login");
    // portal.login(this.credentials as Credentials)
  } else {
    portal.login(credentials);
  }
});

Given("I find my application card", function () {
  cy.wait(90000);
  cy.contains("a", "View your applications").click();
  cy.wait(5000);
  cy.wait("@documentClaimResponse");

  cy.unstash("claimNumber").then((id) => {
    cy.log(id as string);
    cy.get('article[class*="border"]').should("contain.text", id);
  });
});

Given("I am a Leave Admin for the submitted applications", function () {
  cy.unstash("employerFEIN").then((employerFEIN) => {
    cy.task("generateEmployerUsername", employerFEIN).as("employerUsername");
  });
});

Given("I am on the New Application page", function (this: CypressStepThis) {
  cy.unstash("claimNumber").then((claimNumber) => {
    cy.unstash("employerFEIN").then((employerFEIN) => {
      if (this.employerUsername === undefined) {
        throw new Error("Employer username not properly set");
      }
      cy.visit(
        `/employers/applications/new-application/?absence_id=${claimNumber}`
      );
      if (typeof employerFEIN !== "string") {
        throw new Error("Employer username not properly set");
      }
      let password = "";
      if (employerFEIN === "84-7847847") {
        password = "WaynePassword#1";
      } else if (employerFEIN === "99-9999999") {
        password = "UmbrellaPassword#1";
      } else {
        throw new Error("Employer not recognized");
      }
      const credentials: Credentials = {
        username: this.employerUsername,
        password: password,
      };
      portal.employerLogin(credentials);
    });
  });
});

Given("I confirm I am the right person to respond", function () {
  cy.contains("Are you the right person to respond to this application?");
  cy.contains("Yes").click();
  cy.contains("Agree and submit").click();
});

Given(
  "I review the application: I {string} suspect fraud, employee gave {string} notice, and I {string} the claim",
  function (suspectFraud: string, gaveNotice: string, determination: string) {
    switch (suspectFraud) {
      case "do":
        suspectFraud = "Yes (explain below)";
        break;
      case "do not":
        suspectFraud = "No";
        break;
    }
    cy.contains(
      "fieldset",
      "Do you have any reason to suspect this is fraud?"
    ).within(() => {
      cy.contains("label", suspectFraud).click();
    });
    switch (gaveNotice) {
      case "sufficient":
        gaveNotice = "Yes";
        break;
      case "insufficient":
        gaveNotice = "No (explain below)";
        break;
    }
    cy.contains(
      "fieldset",
      "Did the employee give you at least 30 days notice about their leave?"
    ).within(() => {
      cy.contains("label", gaveNotice).click();
    });
    switch (determination) {
      case "approve":
        determination = "Approve";
        break;
      case "deny":
        determination = "Deny (explain below)";
        break;
    }
    cy.contains(
      "fieldset",
      "Have you approved or denied this leave request?"
    ).within(() => {
      cy.contains("label", determination).click();
    });
    if (
      !(
        suspectFraud === "No" &&
        gaveNotice === "Yes" &&
        determination === "Approve"
      )
    ) {
      cy.get('textarea[name="comment"]').type(
        "This is a comment explaning my determination"
      );
    }
    cy.contains("button", "Submit").click();
    cy.contains("Thanks for reviewing the application");
  }
);
