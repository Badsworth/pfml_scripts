import { describeIf } from "../../util";
import { fineos, fineosPages, portal } from "../../actions";
import { format, isBefore, subDays } from "date-fns";
import { config } from "../../actions/common";
import { extractLeavePeriod, extractLeavePeriodType } from "util/claims";

const OTHER_BENEFIT_AMOUNT = 100;
// @note: This can only be tested in environments with the March release
describeIf(
  config("HAS_MARCH_RELEASE") == "true",
  "Other benefits are reported for a claim after payments have been has been made and the leave is in progress",
  {},
  () => {
    const credentials: Credentials = {
      username: "armando+payment_status@lastcallmedia.com",
      password: config("PORTAL_PASSWORD"),
    };

    // Record cancellation after test run to avoid using this claim in future test runs
    after(() => {
      // Confirm findApplication passed - This will avoid failures while attempting to "unstash" if the spec failed before "stashing" "claimToUse"
      if (findApplication.state === "passed") {
        fineos.before();
        cy.unstash<DetailedClaimResponse>("claimToUse").then((claim) => {
          fineosPages.ClaimPage.visit(
            claim.fineos_absence_id
          ).recordCancellation();
        });
      }
    });

    // Look for claims that have payments and are "Complete", meaning leave end date is in the past
    const findApplication = it("Finds a claim from the previous day", () => {
      portal.before();
      portal.loginClaimant(credentials);
      cy.wait("@getApplications").then(({ response }) => {
        const filterCompletedLeaves = (application: ApplicationResponse) => {
          if (!application.leave_details) return false;
          const leaveType = extractLeavePeriodType(application.leave_details);
          let leavePeriods: [Date, Date];
          if (leaveType == "Continuous") {
            leavePeriods = extractLeavePeriod(
              { leave_details: application.leave_details },
              "continuous_leave_periods"
            );
          } else if (leaveType == "Intermittent") {
            leavePeriods = extractLeavePeriod(
              { leave_details: application.leave_details },
              "intermittent_leave_periods"
            );
          } else {
            leavePeriods = extractLeavePeriod(
              { leave_details: application.leave_details },
              "reduced_schedule_leave_periods"
            );
          }
          return (
            isBefore(leavePeriods[1], new Date()) &&
            application.status == "Completed"
          );
        };
        const completedApplications: ApplicationResponse[] =
          response?.body.data.filter(filterCompletedLeaves);
        // sort to use FIFO for claims being used for testing.
        cy.task("findClaim", {
          applications: completedApplications,
          credentials,
          spec: { hasPaidPayments: true, status: "Approved" },
        }).then(([claim]) => {
          cy.stash("claimToUse", claim);
        });
      });
    });

    it(
      "CSR rep can create an offset recovery plan after an overpayment has been generated",
      { retries: 0 },
      () => {
        cy.dependsOnPreviousPass();
        fineos.before();
        // Full Demand
        cy.unstash<DetailedClaimResponse>("claimToUse").then((claim) => {
          if (!claim.absence_periods)
            throw Error("Missing absence periods in claim");
          const { absence_period_end_date } = claim.absence_periods[0];
          fineosPages.ClaimPage.visit(claim.fineos_absence_id)
            .paidLeave((leaveCase) => {
              leaveCase.applyReductions({
                employer_benefits: [
                  {
                    benefit_amount_dollars: OTHER_BENEFIT_AMOUNT,
                    benefit_amount_frequency: "In Total",
                    benefit_type: "Family or medical leave insurance",
                    is_full_salary_continuous: true,
                    benefit_start_date: format(
                      subDays(new Date(absence_period_end_date as string), 7),
                      "yyyy-MM-dd"
                    ),
                    benefit_end_date: format(
                      new Date(absence_period_end_date as string),
                      "yyyy-MM-dd"
                    ),
                  },
                ],
              });
              leaveCase.assertOverpaymentRecord({
                status: "Pending Recovery",
                adjustment: 0,
                amount: OTHER_BENEFIT_AMOUNT,
                outstandingAmount: OTHER_BENEFIT_AMOUNT,
              });
            })
            .tasks((tasks) => {
              tasks.assertIsAssignedToDepartment(
                "Send Overpayment Letter to Claimant (Payee)",
                "DFML Overpayments"
              );
            })
            .paidLeave((paidLeave) => {
              const recoveryPlanPage = paidLeave.createRecoveryPlan(
                OTHER_BENEFIT_AMOUNT,
                "Reimbursement"
              );
              recoveryPlanPage
                .addDocument(
                  "OP-Full Balance Demand",
                  "Overpayment Notice-Full Balance Demand"
                )
                .assertDocumentStatus(
                  "Overpayment Notice-Full Balance Demand",
                  "Completed"
                );
            })
            .tasks((tasks) =>
              tasks.assertTaskExists("Print and Mail Correspondence")
            )
            // Payment Recovery
            .tasks((tasks) => {
              tasks.add("Returned Payment Received");
              tasks.assertIsAssignedToDepartment(
                "Returned Payment Received",
                "DFML Overpayments"
              );
            })
            .paidLeave((paidLeave) => {
              const overpayment = paidLeave.goToOverpaymentCase();
              overpayment.addActualRecovery(OTHER_BENEFIT_AMOUNT);
              overpayment.addDocument(
                "OP-Payment Received",
                "Payment Received-Updated Overpayment Balance"
              );
              // Payment Fully Recovered
              overpayment.assertTaskExists("Print and Mail Correspondence");
              overpayment.addDocument(
                "OP-Notice of Payoff",
                "Overpayment Payoff Notice"
              );
              overpayment.assertDocumentStatus(
                "Overpayment Payoff Notice",
                "Completed"
              );
              overpayment.assertOutstandingOverpaymentBalance(0);
            });
        });
      }
    );
  }
);
