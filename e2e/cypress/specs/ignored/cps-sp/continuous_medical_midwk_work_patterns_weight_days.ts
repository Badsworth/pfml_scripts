import { fineos, fineosPages, portal } from "../../../actions";
import { Submission } from "../../../../src/types";
import {waitForAjaxComplete} from "../../../actions/fineos";

/**
 * This is a test for the weight days in Fineos. The needs for this test is new claimant with no work pattern,
 * start mid-week for the leave period, and submit through the Portal. We had regression for this particular instance in
 * the past between releases.
 */

// @todo Add a clean claimant without any work patterns to this employee (EE) and employer (ER) files that associated to this EE.
// Create a folder directory in the following path `./data/cps-testing/employers.json` and `./data/cps-testing/employees.json`
// Update those files with desired EE/ER to use for testing and update your config.json with that directory for the environment you are using.

describe("Submit a claim through Portal: Verify it creates an absence case in Fineos", () => {
  const submissionTest =
    it("As a claimant, I should be able to submit a claim application through the portal", () => {
      portal.before();
      cy.task("generateClaim", "CPS_MID_WK").then((claim) => {
        cy.stash("claim", claim);
        const application: ApplicationRequestBody = claim.claim;
        const paymentPreference = claim.paymentPreference;
        portal.loginClaimant();
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

  // Going to Fineos and checking the weight days in the claim.
  it("Should check the claim in Fineos and the weight days.", () => {
    cy.dependsOnPreviousPass([submissionTest]);
    fineos.before();
    cy.unstash<DehydratedClaim>("claim").then((claim) => {
      cy.unstash<Submission>("submission").then((submission) => {
      const claimPage = fineosPages.ClaimPage.visit(
        submission.fineos_absence_id
      );
      claimPage.adjudicate((adjudicate) => {
        adjudicate.availability((page) => {
          cy.get(`tr.ListRowSelected`).should("be.visible");
          cy.findByTitle(
            "Manage time for the selected Leave Plan"
          ).click();
          waitForAjaxComplete();
          page.weightDaysCheck(
            claim.metadata?.expected_weight as string + " Weeks"
          )
        });
      });
      });
    });
  });
});
