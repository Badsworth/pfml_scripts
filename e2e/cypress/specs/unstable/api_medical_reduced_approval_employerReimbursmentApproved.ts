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

    const submit = it("Given a submitted claim", () => {
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

    it("CSR Approves the Employer Reimbursement Process", () => {
      fineos.before();
      cy.dependsOnPreviousPass([submit]);
      cy.unstash<DehydratedClaim>("claim").then((claim) => {
        cy.unstash<Submission>("submission").then((sumbmission) => {
          const employerReAmount = 100;
          const claimPage = fineosPages.ClaimPage.visit(
            sumbmission.fineos_absence_id
          );

          claimPage.addActivity("Employer Reimbursement Process");
          claimPage.tasks((task) => {
            task.assertTaskExists("Employer Reimbursement");
          });

          claimPage.addCorrespondenceDocument(
            "Employer Reimbursement Formstack"
          );
          claimPage.addCorrespondenceDocument("Employer Reimbursement Policy");

          // Approve Claim.
          fineos.onTab("Absence Hub");
          claimPage
            .adjudicate((adjudication) => {
              adjudication.evidence((evidence) => {
                // Receive and approve all of the documentation for the claim.
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

          claimPage.paidLeave((paidLeave) => {
            paidLeave.assertAutoPayStatus(false);
          });
          claimPage.tasks((task) => {
            task.closeWithAdditionalSelection(
              "Employer Reimbursement",
              "Reimbursement Approved"
            );
            task.assertTaskExists("Employer Reimbursement Adjustment");
            task.assertTaskExists(
              "Manual Intervention required to Approve Payments"
            );
            task.assertTaskExists("SOM Autopay After Appeal Reminder");
          });

          // Do payment adjustment
          claimPage.paidLeave((paidLeave) => {
            paidLeave.FinancialsBenefitAdjustmentsPage((adjustments) => {
              if (claim.claim.leave_details) {
                const [start_date, end_date] = getLeavePeriod(
                  claim.claim.leave_details
                );
                adjustments.addEmployerReimbursement(
                  start_date,
                  end_date,
                  employerReAmount
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

          claimPage.triggerNotice("SOM Generate Employer Reimbursement Notice");
          //TODO: THERE IS NO WAY TO GET TO THE TASKS->TASKS AFTER GOINT TO TASKS->PROCESSES
          // Both tab tables are named the exact same and FINEOS remembers what sub tab you were
          // on until you leave the absence case
          // eslint-disable-next-line  @typescript-eslint/no-empty-function
          claimPage.paidLeave(() => {});
          claimPage.tasks((task) => {
            task.assertTaskExists("Print and Mail Correspondence");
          });

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
            paidLeave.assertAmountsPending([
              {
                net_payment_amount:
                  parseFloat(expected_weekly_payment) - employerReAmount,
              },
              {
                net_payment_amount: employerReAmount,
                paymentInstances: 2,
              },
            ]);
          });
        });
      });
    });
  }
);
