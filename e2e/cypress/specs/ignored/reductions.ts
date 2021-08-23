import { portal, fineos, fineosPages } from "../../actions";
import { Submission } from "../../../src/types";
import {
  assertIsTypedArray,
  isValidEmployerBenefit,
  isValidOtherIncome,
} from "../../../src/util/typeUtils";

describe("Claim reduction", () => {
  const claimSubmission = it("Given a fully approved claim", () => {
    portal.before();
    cy.task("generateClaim", "MED_OLB").then((claim) => {
      cy.task("submitClaimToAPI", claim).then((response) => {
        cy.stash("claim", claim);
        cy.stash("submission", {
          application_id: response.application_id,
          fineos_absence_id: response.fineos_absence_id,
          timestamp_from: Date.now(),
        });
      });
    });
  });
  const approval =
    it("CPS agent can approve the claim and check for possible reductions", () => {
      cy.dependsOnPreviousPass([claimSubmission]);
      fineos.before();
      cy.unstash<DehydratedClaim>("claim").then(({ documents }) => {
        cy.unstash<Submission>("submission").then((submission) => {
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
            .approve();
        });
      });
    });
  it("CPS Agent can apply reductions to the case", () => {
    cy.dependsOnPreviousPass([claimSubmission, approval]);
    cy.unstash<DehydratedClaim>("claim").then(({ claim }) => {
      cy.unstash<Submission>("submission").then((submission) => {
        fineos.before();
        cy.visit("/");
        fineosPages.ClaimPage.visit(submission.fineos_absence_id).paidLeave(
          (leaveCase) => {
            const { other_incomes, employer_benefits } = claim;
            assertIsTypedArray(other_incomes, isValidOtherIncome);
            assertIsTypedArray(employer_benefits, isValidEmployerBenefit);
            leaveCase
              .applyReductions({ other_incomes, employer_benefits })
              .assertPaymentsMade([{ net_payment_amount: 0 }])
              .assertPaymentAllocations([
                { net_payment_amount: 0 },
                { net_payment_amount: 0 },
              ])
              .assertAmountsPending([{ net_payment_amount: 0 }]);
          }
        );
      });
    });
  });
});
