import { itIf } from "./../../../util";
import { portal, fineos, fineosPages } from "../../../actions";
import { Submission } from "../../../../src/types";
import { assertValidClaim } from "../../../../src/util/typeUtils";
import { addDays, formatISO, startOfWeek, subDays } from "date-fns";
import { config } from "../../../actions/common";
import { calculatePaymentDatePreventingOP } from "../../../actions/fineos.pages";

describe("Submit bonding application via the web portal: Adjudication Approval, recording actual hours & payment checking", () => {
  const submissionTest =
    it("As a claimant, I should be able to submit a intermittent bonding application through the portal", () => {
      portal.before();
      cy.task("generateClaim", "BIAP60").then((claim) => {
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
    it("Leave admin will submit ER approval for employee", () => {
      cy.dependsOnPreviousPass([submissionTest]);
      portal.before();
      cy.unstash<DehydratedClaim>("claim").then((claim) => {
        cy.unstash<Submission>("submission").then((submission) => {
          assertValidClaim(claim.claim);
          portal.loginLeaveAdmin(claim.claim.employer_fein);
          portal.selectClaimFromEmployerDashboard(submission.fineos_absence_id);
          portal.visitActionRequiredERFormPage(submission.fineos_absence_id);
          portal.respondToLeaveAdminRequest(false, true, true);
        });
      });
    });

  const claimApproval = it(
    "CSR rep will approve intermittent bonding application",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass([erApproval]);
      fineos.before();
      cy.unstash<DehydratedClaim>("claim").then((claim) => {
        cy.unstash<Submission>("submission").then(({ fineos_absence_id }) => {
          const claimPage = fineosPages.ClaimPage.visit(fineos_absence_id);
          claimPage.shouldHaveStatus("Eligibility", "Met");
          claimPage.adjudicate((adjudication) => {
            adjudication
              .evidence((evidence) => {
                claim.documents.forEach(({ document_type }) =>
                  evidence.receive(document_type)
                );
              })
              .certificationPeriods((certPeriods) => certPeriods.prefill())
              .acceptLeavePlan();
            adjudication.paidBenefits((paidBenefits) => {
              paidBenefits.assertSitFitOptIn(claim.is_withholding_tax);
            });
          });
          claimPage.shouldHaveStatus("Availability", "As Certified");
          claimPage.approve(
            "Completed",
            config("HAS_APRIL_UPGRADE") === "true"
          );
        });
      });
    }
  );

  const recordingHours = it(
    "CSR rep will record actual hours reported by employee",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass([claimApproval]);
      fineos.before();
      cy.unstash<DehydratedClaim>("claim").then((claim) => {
        cy.unstash<Submission>("submission").then(({ fineos_absence_id }) => {
          const claimPage = fineosPages.ClaimPage.visit(fineos_absence_id);
          claimPage.recordActualLeave((recordActualTime) => {
            // Those are the specific dates fit to the scenario spec.
            // We need those so that fineos approves the actual leave time and generates payments
            const mostRecentSunday = startOfWeek(new Date());
            const actualLeaveStart = formatISO(subDays(mostRecentSunday, 20), {
              representation: "date",
            });
            const actualLeaveEnd = formatISO(
              addDays(subDays(mostRecentSunday, 20), 4),
              {
                representation: "date",
              }
            );
            if (claim.metadata?.spanHoursStart && claim.metadata?.spanHoursEnd)
              recordActualTime.fillTimePeriod({
                startDate: actualLeaveStart,
                endDate: actualLeaveEnd,
                // Just casting to string instead of asserting here.
                timeSpanHoursStart: claim.metadata.spanHoursStart + "",
                timeSpanHoursEnd: claim.metadata.spanHoursEnd + "",
                upgrade: config("HAS_APRIL_UPGRADE") === "true" ? true : false,
              });
            return recordActualTime.nextStep((additionalReporting) => {
              additionalReporting
                .reportAdditionalDetails({
                  reported_by: "Employee",
                  received_via: "Phone",
                  accepted: "Yes",
                  upgrade:
                    config("HAS_APRIL_UPGRADE") === "true" ? true : false,
                })
                .finishRecordingActualLeave();
            });
          });
        });
      });
    }
  );

  it(
    "Should be able to confirm the weekly payment amount for a intermittent schedule",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass([recordingHours]);
      fineos.before();
      cy.unstash<DehydratedClaim>("claim").then((claim) => {
        cy.unstash<Submission>("submission").then((submission) => {
          const payment = claim.metadata
            ?.expected_weekly_payment as unknown as number;
          fineosPages.ClaimPage.visit(submission.fineos_absence_id).paidLeave(
            (leaveCase) => {
              if (config("HAS_FEB_RELEASE") === "true") {
                leaveCase.assertAmountsPending([
                  {
                    net_payment_amount: 831.06,
                    paymentProcessingDates: [
                      calculatePaymentDatePreventingOP(),
                    ],
                  },
                ]);
              } else {
                leaveCase.assertPaymentsMade([{ net_payment_amount: payment }]);
              }
            }
          );
        });
      });
    }
  );
  itIf(
    config("HAS_FEB_RELEASE") === "true",
    "CSR rep will override payment processing date to be schudeuled for day of approval",
    {},
    () => {
      cy.dependsOnPreviousPass([recordingHours]);
      fineos.before();
      cy.unstash<Submission>("submission").then((submission) => {
        fineosPages.ClaimPage.visit(submission.fineos_absence_id).paidLeave(
          (paidLeavePage) => {
            paidLeavePage.editPaymentProcessingDate();
          }
        );
      });
    }
  );
});
