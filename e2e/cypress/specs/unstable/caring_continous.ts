import { portal } from "../../actions";

describe("Submit part one of a caring leave claim through the portal", () => {
  it("As a claimant, I should be able to submit part one of a caring leave claim", () => {
    portal.before();
    cy.task("generateClaim", "CHAP1").then((claim) => {
      cy.stash("claim", claim);
      const application: ApplicationRequestBody = claim.claim;

      const credentials: Credentials = {
        username: Cypress.env("E2E_PORTAL_USERNAME"),
        password: Cypress.env("E2E_PORTAL_PASSWORD"),
      };
      portal.login(credentials);
      portal.goToDashboardFromApplicationsPage();

      // Submit Claim
      portal.startClaim();
      portal.submitClaimPartOne(application);
    });
  });
});
