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

    it("CSR Denies the Employer Reimbursement Process", () => {
      fineos.before();
      cy.dependsOnPreviousPass([submit]);
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
              "Reimbursement Denied"
            );
            task.assertTaskExists("DO NOT USE Autopay After Appeal Reminder");
          });

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
          //TODO: THERE IS NO WAY TO GET TO THE TASKS->TASKS AFTER GOINT TO TASKS->PROCESSES
          // Both tab tables are named the exact same and FINEOS remembers what sub tab you were
          // on until you leave the absence case
          // eslint-disable-next-line @typescript-eslint/no-empty-function
          claimPage.paidLeave(() => {});
          claimPage.tasks((task) => {
            task.assertTaskExists("Print and Mail Correspondence");
          });

          // Step 9 from the spec (appeals flow) was intentionally ommitted.
        });
      });
    });
  }
);
