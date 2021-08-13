import { portal } from "../../../actions";
import { getClaimantCredentials } from "../../../config";

describe("Submit medical pre-birth application via the web portal", () => {
  it("As a claimant, I should be able to submit a continuous medical pre-birth application through the portal", () => {
    portal.before();
    cy.task("generateClaim", "MED_PRE").then((claim) => {
      cy.stash("claim", claim);
      const application = claim.claim;
      const paymentPreference = claim.paymentPreference;

      const credentials = getClaimantCredentials();
      portal.login(credentials);
      portal.goToDashboardFromApplicationsPage();

      // Submit Claim
      portal.startClaim();
      portal.submitClaimPartOne(application);
      portal.waitForClaimSubmission().then((data) => {
        cy.stash("submission", {
          application_id: data.application_id,
          fineos_absence_id: data.fineos_absence_id,
          timestamp_from: Date.now(),
        });
      });
      portal.submitClaimPartsTwoThree(application, paymentPreference);
    });
  });
});
