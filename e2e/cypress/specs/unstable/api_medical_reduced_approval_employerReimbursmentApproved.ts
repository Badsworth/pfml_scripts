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
        fineos.before();
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
        fineos.before();
        cy.dependsOnPreviousPass([submit]);
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
      fineos.before();
      cy.dependsOnPreviousPass([submit, ERProcess]);
      cy.unstash<DehydratedClaim>("claim").then((claim) => {
        cy.unstash<Submission>("submission").then((submission) => {
          const claimPage = fineosPages.ClaimPage.visit(
            submission.fineos_absence_id
          );
          claimPage
            .adjudicate((adjudication) => {
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
            })
            .approve();
          claimPage.tasks((task) => {
            task.closeWithAdditionalSelection(
              "Employer Reimbursement",
              "Reimbursement Approved"
            );
          });
        });
      });
    });

    const ERtrigger =
      it("Add an employer reimbursement to the Paid Leave Case and trigger notice", () => {
        fineos.before();
        cy.dependsOnPreviousPass([submit, ERProcess, approve]);
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
            cy.get("[id^=MENUBAR\\.CaseSubjectMenu]")
              .findByText("Correspondence")
              .click({ force: true })
              .parents("li")
              .findByText("Employer Reimbursement Approval Notice")
              .click();
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

    it("Enable AutoPay along with approve period. Check the adjustment for the payment amount", () => {
      fineos.before();
      cy.dependsOnPreviousPass([submit, ERProcess, approve, ERtrigger]);
      cy.unstash<Submission>("submission").then((submission) => {
        cy.unstash<DehydratedClaim>("claim").then((claim) => {
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
            task.close("SOM Autopay After Appeal Reminder");
          });

          const { expected_weekly_payment } = claim.metadata ?? {};
          if (
            !expected_weekly_payment ||
            typeof expected_weekly_payment !== "string"
          ) {
            throw new Error("expected_weekly_payment must be defined");
          }
          claimPage.paidLeave((paidLeave) => {
            if (config("HAS_FEB_RELEASE") === "true") {
              paidLeave.assertAmountsPending([
                {
                  net_payment_amount:
                    parseFloat(expected_weekly_payment) -
                    (claim.metadata?.employerReAmount as number),
                  paymentInstances: 2,
                },
                {
                  net_payment_amount: claim.metadata
                    ?.employerReAmount as number,
                  paymentInstances: 2,
                },
              ]);
            } else {
              paidLeave.assertAmountsPending([
                {
                  net_payment_amount:
                    parseFloat(expected_weekly_payment) -
                    (claim.metadata?.employerReAmount as number),
                },
                {
                  net_payment_amount: claim.metadata
                    ?.employerReAmount as number,
                  paymentInstances: 2,
                },
              ]);
            }
          });
        });
      });
    });
  }
);
