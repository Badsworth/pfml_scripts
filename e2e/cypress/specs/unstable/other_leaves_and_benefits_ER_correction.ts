import { portal } from "../../actions";
import { getClaimantCredentials, getLeaveAdminCredentials } from "../../config";
import { Submission } from "../../../src/types";
import { isNotNull } from "../../../src/util/typeUtils";
import { config, inFieldsetLabelled } from "../../actions/common";

describe("Claimant uses portal to report other leaves and benefits, receives correction from employer, gets escalated and approved within Fineos", () => {
  if (config("HAS_FINEOS_SP") === "true") {
    const claimSubmission = it("As a claimant, I should be able to report a previous leave, report other benefits, and submit continuos medical leave application through the portal", () => {
      portal.before();
      cy.task("generateClaim", "BHAP1_OLB").then((claim) => {
        cy.stash("claim", claim);
        const application = claim.claim;
        const paymentPreference = claim.paymentPreference;

        const credentials: Credentials = getClaimantCredentials();
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

    it("As a LA, I can report additional accrued leave and employer sponsored benefits", () => {
      cy.dependsOnPreviousPass([claimSubmission]);
      portal.before();
      cy.unstash<DehydratedClaim>("claim").then(({ claim }) => {
        cy.unstash<Submission>("submission").then((submission) => {
          if (isNotNull(claim.employer_fein))
            portal.login(getLeaveAdminCredentials(claim.employer_fein));
          portal.visitActionRequiredERFormPage(submission.fineos_absence_id);
          /**@todo implement ER correction once it's ready [PFMLB-1026]{@link https://lwd.atlassian.net/browse/PFMLPB-1026} */
          cy.contains("label", "Approve").click();
          inFieldsetLabelled(
            "Do you have any additional comments or concerns?",
            () => {
              cy.contains("label", "Yes").click();
            }
          );
          cy.get('textarea[name="comment"]').type(
            "Report additional empoyer benefit"
          );
          cy.contains("button", "Submit").click();
        });
      });
    });

    it(
      "As a CPS Agent, I can review and escalate the claim."
      // { baseUrl: getFineosBaseUrl() },
      // () => {
      //   cy.dependsOnPreviousPass([claimSubmission, erApproval]);
      //   fineos.before();
      //   cy.visit("/");
      //   cy.unstash<DehydratedClaim>("claim").then(({ claim }) => {
      //     cy.unstash<Submission>("submission").then((submission) => {
      //       if (isNotNull(claim.employer_fein))
      //         fineosPages.ClaimPage.visit(submission.fineos_absence_id).approve();
      //     });
      //   });
      // }
    );
  } else {
    it("Does not run", () => {
      cy.log(
        "This test did not execute because this environment does not have the Fineos Service Pack."
      );
    });
  }
});
