import { fineos, portal } from "../../actions";
import { Submission } from "../../../src/types";

describe("Submit a bonding claim with other income and other leave - BHAP1", () => {
  const submit =
    it("As a claimant, I submit a BHAP1 claim with other leave and other income through the portal", () => {
      portal.before();

      cy.task("generateClaim", "BHAP1").then((claim) => {
        if (!claim) {
          throw new Error("Claim Was Not Generated");
        }
        cy.stash("claim", claim);
        const application = claim.claim;
        const paymentPreference = claim.paymentPreference;

        portal.loginClaimant();
        portal.goToDashboardFromApplicationsPage();

        // Submit Claim
        portal.startClaim();
        portal.submitClaimPartOne(application, false);
        portal.waitForClaimSubmission().then((data) => {
          cy.stash("submission", {
            application_id: data.application_id,
            fineos_absence_id: data.fineos_absence_id,
            timestamp_from: Date.now(),
          });
        });
        portal.submitClaimPartsTwoThree(
          application,
          paymentPreference,
          claim.is_withholding_tax
        );
      });
    });
  // Check for Other Leave Document
  it("In Fineos, check for Other Leave E-Form", () => {
    cy.dependsOnPreviousPass([submit]);
    fineos.before();
    cy.unstash<Submission>("submission").then((submission) => {
      cy.visit("/");
      fineos.findOtherLeaveEForm(submission.fineos_absence_id);
    });
  });
});
