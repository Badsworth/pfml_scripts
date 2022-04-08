import { fineos, fineosPages, portal } from "../../../actions";
import {
  Submission,
  ValidConcurrentLeave,
  ValidEmployerBenefit,
} from "../../../../src/types";
import {
  assertIsTypedArray,
  assertValidClaim,
  isValidEmployerBenefit,
  isValidOtherIncome,
  isValidPreviousLeave,
} from "../../../../src/util/typeUtils";
import { config } from "../../../actions/common";
import { calculatePaymentDatePreventingOP } from "../../../actions/fineos.pages";

// Used for stashing generated benefit and leave
type LeaveAdminchanges = {
  employerReportedBenefit: ValidEmployerBenefit;
  employerReportedConcurrentLeave: ValidConcurrentLeave;
};

describe("Claimant uses portal to report other leaves and benefits, receives correction from employer, gets escalated and approved within Fineos", () => {
  const claimSubmission =
    it("As a claimant, I should be able to report a previous leave, report other benefits, and submit continuos medical leave application through the portal", () => {
      portal.before();
      cy.task("generateClaim", "BHAP1_OLB").then((claim) => {
        const employerReportedBenefit = claim.claim.employer_benefits?.[0];
        delete claim.claim.employer_benefits;
        const employerReportedConcurrentLeave = claim.claim.concurrent_leave;
        delete claim.claim.concurrent_leave;
        cy.stash("amendments", {
          employerReportedBenefit,
          employerReportedConcurrentLeave,
        });
        cy.stash("claim", claim);
        const application = claim.claim;
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

  const erApproval =
    it("As a LA, I can report additional accrued leave and employer sponsored benefits", () => {
      cy.dependsOnPreviousPass([claimSubmission]);
      portal.before();
      cy.unstash<DehydratedClaim>("claim").then(({ claim }) => {
        cy.unstash<Submission>("submission").then((submission) => {
          cy.unstash<LeaveAdminchanges>("amendments").then(
            ({ employerReportedBenefit, employerReportedConcurrentLeave }) => {
              assertValidClaim(claim);
              portal.loginLeaveAdmin(claim.employer_fein);
              portal.visitActionRequiredERFormPage(
                submission.fineos_absence_id
              );

              assertIsTypedArray(
                claim.previous_leaves_other_reason,
                isValidPreviousLeave
              );
              // Check the employee reported previous leave is here.
              portal.assertPreviousLeave(claim.previous_leaves_other_reason[0]);

              portal.amendPreviousLeave(claim.previous_leaves_other_reason[0], {
                ...claim.previous_leaves_other_reason[0],
                leave_reason: "Pregnancy",
              });

              portal.addEmployerBenefit(employerReportedBenefit);
              portal.addConcurrentLeave(employerReportedConcurrentLeave);
              portal.respondToLeaveAdminRequest(false, true, true);
            }
          );
        });
      });
    });

  const approval =
    it("As a CPS Agent, I can review and approve the claim, then apply reductions ", () => {
      cy.dependsOnPreviousPass([claimSubmission, erApproval]);
      fineos.before();
      cy.unstash<DehydratedClaim>("claim").then(({ claim, documents }) => {
        cy.unstash<Submission>("submission").then((submission) => {
          cy.unstash<LeaveAdminchanges>("amendments").then(
            ({ employerReportedBenefit, employerReportedConcurrentLeave }) => {
              claim.employer_benefits = [employerReportedBenefit];
              claim.concurrent_leave = employerReportedConcurrentLeave;
              assertValidClaim(claim);
              const claimPage = fineosPages.ClaimPage.visit(
                submission.fineos_absence_id
              )
                .tasks((tasks) => {
                  // Check all of the appropriate tasks have been generated
                  tasks.assertTaskExists("Employee Reported Other Leave");
                  tasks.assertTaskExists("Employee Reported Other Income");
                  tasks.assertTaskExists("Employer Conflict Reported");
                  // Add escalation tasks and check they are assigned appropriately
                  tasks
                    .add("Escalate Employer Reported Other Income")
                    .assertIsAssignedToUser(
                      "Escalate Employer Reported Other Income",
                      "DFML Program Integrity"
                    )
                    .assertIsAssignedToDepartment(
                      "Escalate Employer Reported Other Income",
                      "DFML Program Integrity"
                    );
                  tasks
                    .add("Escalate employer reported past leave")
                    .assertIsAssignedToUser(
                      "Escalate employer reported past leave",
                      "DFML Program Integrity"
                    )
                    .assertIsAssignedToDepartment(
                      "Escalate employer reported past leave",
                      "DFML Program Integrity"
                    );
                })
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
                    .paidBenefits((paidBenefits) => {
                      paidBenefits.assertSitFitOptIn(true);
                    })
                    .acceptLeavePlan();
                });
              claimPage.approve(
                "Approved",
                config("HAS_APRIL_UPGRADE") === "true"
              );
              claimPage.paidLeave((leaveCase) => {
                const { other_incomes, employer_benefits } = claim;
                assertIsTypedArray(other_incomes, isValidOtherIncome);
                assertIsTypedArray(employer_benefits, isValidEmployerBenefit);
                leaveCase.applyReductions({
                  other_incomes,
                  employer_benefits,
                });
              });
            }
          );
        });
      });
    });
  it(
    "Payments appear in paid leave case with the expected amounts",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass([approval]);
      fineos.before();
      cy.unstash<Submission>("submission").then((submission) => {
        fineosPages.ClaimPage.visit(submission.fineos_absence_id).paidLeave(
          (leaveCase) => {
            const paymentDates = Array<Date>(2).fill(
              calculatePaymentDatePreventingOP()
            );
            leaveCase.assertPaymentsMade([]).assertAmountsPending([
              // retroactive SIT/FIT appear in amounts pending with processing date of today
              {
                net_payment_amount: 58.43,
                paymentInstances: 2,
                paymentProcessingDates: paymentDates,
              },
              {
                net_payment_amount: 29.22,
                paymentInstances: 2,
                paymentProcessingDates: paymentDates,
              },
              {
                net_payment_amount: 496.66,
                paymentInstances: 2,
                paymentProcessingDates: paymentDates,
              },
            ]);
          }
        );
      });
    }
  );
});
