import { fineos, fineosPages, portal } from "../../../actions";
import { Submission } from "../../../../src/types";
import { assertValidClaim } from "../../../../src/util/typeUtils";
import { getDocumentReviewTaskName } from "../../../../src/util/documents";
import { config } from "../../../actions/common";

describe("Submit caring application via the web portal: Adjudication Approval & payment checking", () => {
  const submissionTest =
    it("As a claimant, I should be able to submit a continuous caring application through the portal", () => {
      portal.before();
      cy.task("generateClaim", "CCAP90").then((claim) => {
        cy.stash("claim", claim);
        const application: ApplicationRequestBody = claim.claim;
        const paymentPreference = claim.paymentPreference;

        portal.loginClaimant();
        portal.skipLoadingClaimantApplications();

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

  it("Leave admin will submit ER approval for employee", () => {
    cy.dependsOnPreviousPass([submissionTest]);
    portal.before();
    cy.unstash<DehydratedClaim>("claim").then((claim) => {
      cy.unstash<Submission>("submission").then((submission) => {
        assertValidClaim(claim.claim);
        portal.loginLeaveAdmin(claim.claim.employer_fein);
        portal.selectClaimFromEmployerDashboard(submission.fineos_absence_id);
        portal.visitActionRequiredERFormPage(submission.fineos_absence_id);
        portal.respondToLeaveAdminRequest(false, true, true, true);
      });
    });
  });

  it("CSR rep will approve continous caring application", () => {
    cy.dependsOnPreviousPass();
    fineos.before();
    cy.unstash<Submission>("submission").then(({ fineos_absence_id }) => {
      cy.unstash<DehydratedClaim>("claim").then((claim) => {
        cy.tryCount().then((tryCount) => {
          if (tryCount > 0) {
            fineos.assertClaimStatus("Approved");
            return;
          }
          fineosPages.ClaimPage.visit(fineos_absence_id)
            .tasks((tasks) => {
              claim.documents.forEach((doc) =>
                tasks.assertTaskExists(
                  getDocumentReviewTaskName(doc.document_type)
                )
              );
            })
            .shouldHaveStatus("Applicability", "Applicable")
            .shouldHaveStatus("Eligibility", "Met")
            .adjudicate((adjudication) => {
              adjudication
                .evidence((evidence) =>
                  claim.documents.forEach((doc) =>
                    evidence.receive(doc.document_type)
                  )
                )
                .certificationPeriods((certPreiods) => certPreiods.prefill())
                .acceptLeavePlan();
            })
            .approve("Approved", config("HAS_APRIL_UPGRADE") === "true");
        });
      });
    });
  });

  it(
    "Should be able to confirm the weekly payment amount and check Ownership is Assigned To",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass();
      fineos.before();

      cy.unstash<DehydratedClaim>("claim").then((claim) => {
        cy.unstash<Submission>("submission").then((submission) => {
          const payment = claim.metadata
            ?.expected_weekly_payment as unknown as number;
          fineosPages.ClaimPage.visit(submission.fineos_absence_id).paidLeave(
            (leaveCase) => {
              leaveCase.assertOwnershipAssignTo("DFML Program Integrity");
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
});
