import { config } from "./../../actions/common";
import { portal } from "./../../actions";

describe("Submit caring application via the web portal: Adjudication Approval & payment checking", () => {
    it("As a claimant, I should be able to submit a continous caring application through the portal", () => {
      portal.before();
      cy.task("generateCredentials").then((credentials) => {
        portal.registerAsClaimant(credentials);
        portal.login(credentials);
        portal.assertLoggedIn();
        cy.get('button[type="submit"]').contains("Agree and continue").click();
        cy.wait(1000)
        cy.task("generateClaim", "BHAP1").then((claim) => {
            cy.stash("claim", claim);
            const application: ApplicationRequestBody = claim.claim;
            const paymentPreference = claim.paymentPreference;

            portal.login(credentials);
            portal.startApplicationForFirstTime();
            cy.contains("button", "I understand and agree").click();
    
            // Submit Claim
            portal.clickChecklistButton("Verify your identification");
            portal.verifyIdentity(application);            
            cy.wait(5000);
            cy.clearCookies();
            portal.before();
        cy.task("generateCredentials").then((new_credentials) => {
            portal.registerAsClaimant(new_credentials);
            portal.login(new_credentials);
            portal.assertLoggedIn();
            cy.get('button[type="submit"]').contains("Agree and continue").click();
            const application: ApplicationRequestBody = claim.claim;
            const paymentPreference = claim.paymentPreference;

            portal.login(new_credentials);
            portal.startApplicationForFirstTime();
            cy.contains("button", "I understand and agree").click();
    
            // Submit Claim
            portal.submitClaimPartOne(application);
        });
        });
    });
  });
});
