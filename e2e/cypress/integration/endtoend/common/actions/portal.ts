export function onPage(page: string): void {
  cy.url().should("include", `/claims/${page}`);
}

export function submittingClaimType(claimType: string): void {
  cy.fixture(claimType).then((application) => {
    cy.wrap(application).as("application");
  });
}

export function submitClaimDirectlyToAPI(scenario: string): void {
  cy.fixture(scenario).then({ timeout: 40000 }, (app) => {
    console.log("submitting", app);
    cy.task("submitClaimToAPI", app).then((fineosId) => {
      cy.stash("claimNumber", fineosId);
      console.log("submitted", fineosId);
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
