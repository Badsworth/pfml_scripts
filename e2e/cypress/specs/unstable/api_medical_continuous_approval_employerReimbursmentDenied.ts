import { fineos, portal, fineosPages } from "../../actions";
import { Submission } from "../../../src/types";
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
      it("CSR starts the Employer Reimbursement Process and adds documents and approves claim", () => {
        cy.dependsOnPreviousPass([submit]);
        fineos.before();
        cy.unstash<DehydratedClaim>("claim").then((claim) => {
          cy.unstash<Submission>("submission").then((sumbmission) => {
            const claimPage = fineosPages.ClaimPage.visit(
              sumbmission.fineos_absence_id
            );

            claimPage.addActivity("Employer Reimbursement Process");
            claimPage.tasks((task) => {
              task.assertTaskExists("Employer Reimbursement");
            });
            claimPage.leaveDetails((leaveDetails) => {
              leaveDetails
                .editLeave()
                .paidBenefits((paidBenefits) => {
                  paidBenefits.assertAutoPayStatus(false);
                })
                .exitWithoutSaving();
            });

            claimPage.addCorrespondenceDocument(
              "Employer Reimbursement Formstack"
            );
            claimPage.addCorrespondenceDocument(
              "Employer Reimbursement Policy"
            );

            // Approve Claim.
            fineos.onTab("Absence Hub");
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
            if (config("HAS_APRIL_UPGRADE") === "true") {
              claimPage.approve("Approved", true);
            } else {
              claimPage.approve("Approved", false);
            }
          });
        });
      });

    it("Deny the employer reimbursement to the Paid Leave Case and trigger notice", () => {
      cy.dependsOnPreviousPass([submit, ERProcess]);
      fineos.before();
      cy.unstash<Submission>("submission").then((sumbmission) => {
        const claimPage = fineosPages.ClaimPage.visit(
          sumbmission.fineos_absence_id
        );
        claimPage.paidLeave((paidLeave) => {
          paidLeave.assertAutoPayStatus(false);
        });
        claimPage.tasks((task) => {
          task.closeWithAdditionalSelection(
            "Employer Reimbursement",
            "Reimbursement Denied"
          );
          // FINEOS February release made a change to the task name. But the FINEOS
          // January release has the another name for this task.
          if (config("HAS_FEB_RELEASE") === "true") {
            task.assertTaskExists("SOM Autopay After Appeal Reminder");
          } else {
            task.assertTaskExists("DO NOT USE Autopay After Appeal Reminder");
          }
          cy.get("[id^=MENUBAR\\.CaseSubjectMenu]")
            .findByText("Correspondence")
            .click({ force: true })
            .parents("li")
            .findByText("Employer Reimbursement Denial Notice")
            .click();
          fineos.clickBottomWidgetButton("Next");
          claimPage.documents((document) => {
            document.setDocumentComplete(
              "Employer Reimbursement Denial Notice"
            );
          });

          claimPage.triggerNotice("SOM Generate Employer Reimbursement Notice");
          claimPage.tasks((task) => {
            task.returnSubTasksTab();
            task.assertTaskExists("Print and Mail Correspondence");
          });
        });
      });
    });
  }
);
