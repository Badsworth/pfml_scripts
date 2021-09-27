import { Submission } from "../../../../src/types";
import {
  assertIsTypedArray,
  assertValidClaim,
  isValidConcurrentLeave,
  isValidEmployerBenefit,
  isValidPreviousLeave,
} from "../../../../src/util/typeUtils";
import { fineos, fineosPages, portal } from "../../../actions";

describe("Claimant can call call-center to submit a claim for leave with other leaves and benefits", () => {
  const claimSubmission =
    it("CPS Agent can enter a claim with Concurrent (employer sponsored) leave and employer sponsored benefits", () => {
      fineos.before();
      cy.visit("/");
      cy.task("generateClaim", "CONTINUOUS_MEDICAL_OLB").then((claim) => {
        cy.stash("claim", claim);
        assertValidClaim(claim.claim);
        const claimantPage = fineosPages.ClaimantPage.visit(
          claim.claim.tax_identifier
        );

        claimantPage
          .createNotification(claim.claim)
          .then((fineos_absence_id) => {
            cy.stash("submission", {
              timestamp_from: Date.now(),
              fineos_absence_id,
            });

            fineosPages.ClaimPage.visit(fineos_absence_id)
              .documents((documentsPage) => {
                const {
                  employer_benefits,
                  previous_leaves_other_reason,
                  previous_leaves_same_reason,
                  other_incomes,
                  concurrent_leave,
                } = claim.claim;
                documentsPage
                  .submitOtherBenefits({
                    employer_benefits: employer_benefits?.filter(
                      (b) => b.benefit_type !== "Accrued paid leave"
                    ),
                    other_incomes,
                  })
                  .submitOtherLeaves({
                    previous_leaves_other_reason,
                    previous_leaves_same_reason,
                    concurrent_leave,
                  });
              })
              .adjudicate((adjudicate) => {
                adjudicate.evidence((evidence) => {
                  claim.documents.forEach(({ document_type }) =>
                    evidence.receive(document_type)
                  );
                });
              });
          });
      });
    });
  it("LA can review and deny the claim", () => {
    cy.dependsOnPreviousPass([claimSubmission]);
    portal.before();
    cy.unstash<DehydratedClaim>("claim").then(({ claim }) => {
      cy.unstash<Submission>("submission").then((submission) => {
        assertValidClaim(claim);
        portal.loginLeaveAdmin(claim.employer_fein);
        portal.visitActionRequiredERFormPage(submission.fineos_absence_id);
        // Check we have the previous leave from fineos
        assertIsTypedArray(
          claim.previous_leaves_other_reason,
          isValidPreviousLeave
        );
        portal.assertPreviousLeave(claim.previous_leaves_other_reason[0]);
        // Check we have the employer benefits from fineos
        assertIsTypedArray(claim.employer_benefits, isValidEmployerBenefit);
        portal.assertEmployerBenefit(claim.employer_benefits[0]);

        // Check we have concurrent leave from fineos
        if (isValidConcurrentLeave(claim.concurrent_leave))
          portal.assertConcurrentLeave(claim.concurrent_leave);
        // Deny the claim
        portal.respondToLeaveAdminRequest(false, true, false, false);
      });
    });
  });
});
