import { fineos, portal, fineosPages } from "../../actions";
import { Submission } from "../../../src/types";
import { getLeavePeriod } from "../../../src/util/claims";
import { DehydratedClaim } from "../../../src/generation/Claim";
import { config } from "../../actions/common";

//Dont run if env doesn't have the Jan release or in training until next data load
(config("HAS_EMPLOYER_REIMBURSEMENTS") === "true" ? describe : describe.skip)(
  "Employer Reimbursement Denial",
  () => {
    after(() => {
      portal.deleteDownloadsFolder();
    });

    const submit =
      it("Submit a claim through the API for a Serious Health Condition - Employee with 4 wks", () => {
        // Submit a claim via the API, including Employer Response.
        cy.task("generateClaim", "MED_ERRE").then((claim) => {
          cy.stash("claim", claim);
          cy.task("submitClaimToAPI", claim).then((res) => {
            cy.stash("submission", {
              application_id: res.application_id,
              fineos_absence_id: res.fineos_absence_id,
              timestamp_from: Date.now(),
            });
          });
        });
      });

    const ERProcess =
      it("CSR starts the Employer Reimbursement Process and adds documents", () => {
        cy.dependsOnPreviousPass([submit]);
        fineos.before();
        cy.unstash<Submission>("submission").then((submission) => {
          const claimPage = fineosPages.ClaimPage.visit(
            submission.fineos_absence_id
          );

          claimPage.addActivity("Employer Reimbursement Process");
          claimPage.tasks((task) => {
            task.assertTaskExists("Employer Reimbursement");
          });

          claimPage.addCorrespondenceDocument(
            "Employer Reimbursement Formstack"
          );
          claimPage.addCorrespondenceDocument("Employer Reimbursement Policy");
        });
      });

    const approve = it("CSR approves the leave plan and absence case", () => {
      cy.dependsOnPreviousPass([submit, ERProcess]);
      fineos.before();
      cy.tryCount().then((tryCount) => {
        cy.unstash<DehydratedClaim>("claim").then((claim) => {
          cy.unstash<Submission>("submission").then((submission) => {
            const claimPage = fineosPages.ClaimPage.visit(
              submission.fineos_absence_id
            );
            if (tryCount > 0) {
              fineos.assertClaimStatus("Approved");
              claimPage.tasks((task) => {
                task.closeWithAdditionalSelection(
                  "Employer Reimbursement",
                  "Reimbursement Approved"
                );
              });
              return;
            }
            claimPage.adjudicate((adjudication) => {
              adjudication.evidence((evidence) => {
                // Receive and approve all documents for the claim.
                claim.documents.forEach((document) => {
                  evidence.receive(document.document_type);
                });
              });
              adjudication.certificationPeriods((certificationPeriods) =>
                certificationPeriods.prefill()
              );
              adjudication.acceptLeavePlan();
            });
            claimPage.approve(
              "Approved",
              config("HAS_APRIL_UPGRADE") === "true"
            );
            claimPage.tasks((task) => {
              task.closeWithAdditionalSelection(
                "Employer Reimbursement",
                "Reimbursement Approved"
              );
            });
          });
        });
      });
    });

    const ERtrigger =
      it("Add an employer reimbursement to the Paid Leave Case and trigger notice", () => {
        cy.dependsOnPreviousPass([submit, ERProcess, approve]);
        fineos.before();
        cy.unstash<Submission>("submission").then((submission) => {
          cy.unstash<DehydratedClaim>("claim").then((claim) => {
            const claimPage = fineosPages.ClaimPage.visit(
              submission.fineos_absence_id
            );
            claimPage.paidLeave((paidLeave) => {
              paidLeave.FinancialsBenefitAdjustmentsPage((adjustments) => {
                if (claim.claim.leave_details) {
                  const [start_date, end_date] = getLeavePeriod(
                    claim.claim.leave_details
                  );
                  adjustments.addEmployerReimbursement(
                    start_date,
                    end_date,
                    claim.metadata?.employerReAmount as number
                  );
                }
              });
            });
            claimPage.tasks((task) => {
              task.close("Employer Reimbursement Adjustment");
            });
            // Force in the click at the end of the chainable is causing
            // issue in cps-preview and stage environments.
            if (config("HAS_APRIL_UPGRADE") === "true") {
              cy.get("[id^=MENUBAR\\.CaseSubjectMenu]")
                .findByText("Correspondence")
                .click({ force: true })
                .parents("li")
                .findByText("Employer Reimbursement Approval Notice")
                .click({ force: true });
            } else {
              cy.get("[id^=MENUBAR\\.CaseSubjectMenu]")
                .findByText("Correspondence")
                .click({ force: true })
                .parents("li")
                .findByText("Employer Reimbursement Approval Notice")
                .click();
            }
            fineos.clickBottomWidgetButton("Next");
            claimPage.documents((document) => {
              document.setDocumentComplete(
                "Employer Reimbursement Approval Notice"
              );
            });
            claimPage.triggerNotice(
              "SOM Generate Employer Reimbursement Notice"
            );
            claimPage.tasks((task) => {
              task.returnSubTasksTab();
              task.assertTaskExists("Print and Mail Correspondence");
            });
          });
        });
      });

    const enablePayment =
      it("Enable AutoPay along with approve period to all the payment to show", () => {
        cy.dependsOnPreviousPass([submit, ERProcess, approve, ERtrigger]);
        fineos.before();
        cy.unstash<Submission>("submission").then((submission) => {
          const claimPage = fineosPages.ClaimPage.visit(
            submission.fineos_absence_id
          );
          claimPage.paidLeave((paidLeave) => {
            paidLeave.changeAutoPayStatus(true);
            paidLeave.assertAutoPayStatus(true);
          });

          claimPage.paidLeave((paidLeave) => {
            paidLeave.approvePeriod();
            paidLeave.tasks((task) => {
              task.close("Manual Intervention required to Approve Periods");
            });
          });
          claimPage.tasks((task) => {
            task.close("Manual Intervention required to Approve Payments");
            // The task has changed in DT4 from SOM Autopay After Appeal Reminder to Autopay After Appeal Reminder.
            // Waiting on a response to see if this is the final way that task will display or being updated.
            if (config("HAS_APRIL_UPGRADE") === "true") {
              task.close("Autopay After Appeal Reminder");
            } else {
              task.close("SOM Autopay After Appeal Reminder");
            }
          });
        });
      });

    it("Check the adjustment for the payment amount", { retries: 0 }, () => {
      cy.dependsOnPreviousPass([enablePayment]);
      fineos.before();
      cy.unstash<Submission>("submission").then((submission) => {
        cy.unstash<DehydratedClaim>("claim").then((claim) => {
          const claimPage = fineosPages.ClaimPage.visit(
            submission.fineos_absence_id
          );
          const { expected_weekly_payment } = claim.metadata ?? {};
          if (
            !expected_weekly_payment ||
            typeof expected_weekly_payment !== "string"
          ) {
            throw new Error("expected_weekly_payment must be defined");
          }
          claimPage.paidLeave((paidLeave) => {
            paidLeave.assertAmountsPending([
              {
                net_payment_amount:
                  parseFloat(expected_weekly_payment) -
                  (claim.metadata?.employerReAmount as number),
                paymentInstances: 2,
              },
              {
                net_payment_amount: claim.metadata?.employerReAmount as number,
                paymentInstances: 2,
              },
            ]);
          });
        });
      });
    });
  }
);
