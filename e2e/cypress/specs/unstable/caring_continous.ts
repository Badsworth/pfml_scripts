import { portal } from "../../actions";
import { config } from "../../actions/common";

describe("Submit part one of a caring leave claim through the portal", () => {
  if (config("HAS_FINEOS_SP") === "true") {
    it("As a claimant, I should be able to submit part one of a caring leave claim", () => {
      portal.before();
      cy.task("generateClaim", "CHAP1").then((claim) => {
        cy.stash("claim", claim);
        const paymentPreference = claim.paymentPreference;

        const application: ApplicationRequestBody = claim.claim;

        const credentials: Credentials = {
          username: config("PORTAL_USERNAME"),
          password: config("PORTAL_PASSWORD"),
        };
        portal.login(credentials);
        portal.goToDashboardFromApplicationsPage();

        // Submit Claim
        portal.startClaim();
        portal.submitClaimPartOne(application);
        portal.waitForClaimSubmission();
        portal.submitPartsTwoThreeNoLeaveCert(paymentPreference);
      });
    });
  } else {
    it("Does not run", () => {
      cy.log(
        "This test did not execute because this environment does not have the Fineos Service Pack."
      );
    });
  }
});
