import { fineos, fineosPages, portal } from "../../../actions";
import { getFineosBaseUrl, getLeaveAdminCredentials } from "../../../config";
import { Submission } from "../../../../src/types";
import { config } from "../../../actions/common";
import { assertValidClaim } from "../../../../src/util/typeUtils";

describe("Submit caring application via the web portal: Adjudication Approval & payment checking", () => {
  if (config("HAS_FINEOS_SP") === "true") {
    const submissionTest = it("As a claimant, I should be able to submit a continous caring application through the portal", () => {
      portal.before();
      cy.task("generateClaim", "CCAP90").then((claim) => {
        cy.stash("claim", claim);
        const application: ApplicationRequestBody = claim.claim;
        const paymentPreference = claim.paymentPreference;

        const credentials: Credentials = {
          username: config("PORTAL_USERNAME"),
          password: config("PORTAL_PASSWORD"),
        };
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

    it("Leave admin will submit ER approval for employee", () => {
      cy.dependsOnPreviousPass([submissionTest]);
      portal.before();
      cy.unstash<DehydratedClaim>("claim").then((claim) => {
        cy.unstash<Submission>("submission").then((submission) => {
          assertValidClaim(claim.claim);
          portal.login(getLeaveAdminCredentials(claim.claim.employer_fein));
          portal.selectClaimFromEmployerDashboard(
            submission.fineos_absence_id,
            "--"
          );
          portal.visitActionRequiredERFormPage(submission.fineos_absence_id);
          portal.respondToLeaveAdminRequest(false, true, true, true);
        });
      });
    });

    it(
      "CSR rep will approve continous caring application",
      { retries: 0, baseUrl: getFineosBaseUrl() },
      () => {
        cy.dependsOnPreviousPass();
        fineos.before();
        cy.visit("/");
        cy.unstash<Submission>("submission").then((submission) => {
          fineos.claimAdjudicationFlow(
            submission.fineos_absence_id,
            "Care for a Family Member",
            true
          );
        });
      }
    );

    it(
      "Should be able to confirm the weekly payment amount",
      { baseUrl: getFineosBaseUrl() },
      () => {
        cy.dependsOnPreviousPass();
        fineos.before();
        cy.visit("/");

        cy.unstash<DehydratedClaim>("claim").then((claim) => {
          cy.unstash<Submission>("submission").then((submission) => {
            const payment = (claim.metadata
              ?.expected_weekly_payment as unknown) as number;
            fineosPages.ClaimPage.visit(submission.fineos_absence_id).paidLeave(
              (leaveCase) => {
                leaveCase.assertAmountsPending([
                  {
                    net_payment_amount: payment,
                  },
                ]);
              }
            );
          });
        });
      }
    );
  } else {
    it("Does not run", () => {
      cy.log(
        "This test did not execute because this environment does not have the Fineos Service Pack."
      );
    });
  }
});
