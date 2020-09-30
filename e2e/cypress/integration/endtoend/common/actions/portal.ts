import { Credentials } from "@/types";
import PortalSubmitter from "@/simulation/PortalSubmitter";

export function onPage(page: string): void {
  cy.url().should("include", `/claims/${page}`);
}

export function submittingClaimType(claimType: string): void {
  cy.fixture(claimType).then((application) => {
    cy.wrap(application).as("application");
  });
}

export function submitClaimDirectlyToAPI(scenario: string): void {
  const submitter = new PortalSubmitter({
    ClientId: Cypress.env("E2E_COGNITO_CLIENTID"),
    UserPoolId: Cypress.env("E2E_COGNITO_POOL"),
    Username: Cypress.env("E2E_PORTAL_USERNAME"),
    Password: Cypress.env("E2E_PORTAL_PASSWORD"),
    ApiBaseUrl: Cypress.env("E2E_API_BASE_URL"), // verify api base url
  });
  cy.fixture(scenario).then((application) => {
    console.log("application", application);
    submitter
      .submit(application)
      .then((fineosId) => {
        console.log("Submitted claim with id", fineosId);
        // cy.stash("claimNumber", fineosId);
      })
      .catch((err) => {
        console.error("Failed to submit claim:", err);
      });
  });
}

export function login(credentials: Credentials): void {
  // Alias the credentials for later use.
  cy.wrap(credentials).as("credentials");
  cy.visit("/");
  cy.labelled("Email address").type(credentials.username);
  cy.labelled("Password").typeMasked(credentials.password);
  cy.contains("button", "Log in").click();
}

export function assertLoggedIn(): void {
  cy.contains("button", "Log out").should("be.visible");
}

export function startClaim(): void {
  cy.get('[href="/claims/start/"]').click();
}

export function agreeToStart(): void {
  cy.contains("button", "I understand and agree").click();
}

export function hasClaimId(): void {
  cy.url().should("include", "claim_id");
}
