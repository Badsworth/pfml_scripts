import { Submission } from "../../../src/types";
import { extractLeavePeriod } from "../../../src/util/claims";
import {
  assertIsTypedArray,
  assertValidClaim,
  isValidEmployerBenefit,
  isValidOtherIncome,
} from "../../../src/util/typeUtils";
import { fineos, fineosPages, portal } from "../../actions";
import { config } from "../../actions/common";
import { getFineosBaseUrl, getLeaveAdminCredentials } from "../../config";

describe("Claimant can call call-center to submit a claim for leave with other leaves and benefits", () => {
  if (config("FINEOS_HAS_UPDATED_EFORMS") === "true") {
    const claimSubmission = it(
      "CPS Agent can enter a claim with Concurrent (employer sponsored) leave and employer sponsored benefits",
      { baseUrl: getFineosBaseUrl() },
      () => {
        fineos.before();
        cy.visit("/");
        cy.task("generateClaim", "CONTINUOUS_MEDICAL_OLB").then((claim) => {
          cy.stash("claim", claim);
          assertValidClaim(claim.claim);
          fineos.searchClaimantSSN(claim.claim.tax_identifier);
          fineos.clickBottomWidgetButton("OK");
          fineos.assertOnClaimantPage(
            claim.claim.first_name,
            claim.claim.last_name
          );
          const [startDate, endDate] = extractLeavePeriod(
            claim.claim,
            "continuous_leave_periods"
          );
          fineos.createNotification(startDate, endDate, "medical", claim.claim);
          cy.get("a[name*='CaseMapWidget']")
            .invoke("text")
            .then((text) => {
              const fineos_absence_id = text.slice(24);

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
      }
    );
    /**
     * @todo Functionality needed for these tests will be available starting June 18th.
     */
    const erApproval = it("LA can review and approve a claim", () => {
      cy.dependsOnPreviousPass([claimSubmission]);
      portal.before();
      cy.unstash<DehydratedClaim>("claim").then(({ claim }) => {
        cy.unstash<Submission>("submission").then((submission) => {
          assertValidClaim(claim);
          portal.login(getLeaveAdminCredentials(claim.employer_fein));
          portal.visitActionRequiredERFormPage(submission.fineos_absence_id);
          portal.respondToLeaveAdminRequest(false, true, true, false);
        });
      });
    });
    xit(
      "CPS agent can approve the claim and check for possible reductions",
      { baseUrl: getFineosBaseUrl() },
      () => {
        cy.dependsOnPreviousPass([claimSubmission, erApproval]);
        fineos.before();
        cy.visit("/");
        cy.unstash<DehydratedClaim>("claim").then(({ claim, documents }) => {
          cy.unstash<Submission>("submission").then((submission) => {
            assertValidClaim(claim);
            fineosPages.ClaimPage.visit(submission.fineos_absence_id)
              .adjudicate((adjudication) => {
                adjudication
                  .evidence((evidence) => {
                    documents.forEach(({ document_type }) => {
                      evidence.receive(document_type);
                    });
                  })
                  .certificationPeriods((certification) => {
                    certification.prefill();
                  })
                  .acceptLeavePlan();
              })
              .approve()
              .paidLeave((leaveCase) => {
                const { other_incomes, employer_benefits } = claim;
                assertIsTypedArray(other_incomes, isValidOtherIncome);
                assertIsTypedArray(employer_benefits, isValidEmployerBenefit);
                leaveCase
                  .applyReductions({ other_incomes, employer_benefits })
                  .assertPaymentsMade([{ net_payment_amount: 1100 }])
                  .assertPaymentAllocations([
                    { net_payment_amount: 550 },
                    { net_payment_amount: 550 },
                  ])
                  .assertAmountsPending([{ net_payment_amount: 550 }]);
              });
          });
        });
      }
    );
  } else {
    it("Does not run", () => {
      cy.log(
        "This test did not execute because this environment does not have the updated Fineos eForms."
      );
    });
  }
});
