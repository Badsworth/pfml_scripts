import { Submission } from "../../../../src/types";
import { email, fineos, fineosPages, portal } from "../../../actions";
import { config } from "../../../actions/common";
import { getClaimantCredentials } from "../../../config";
import { describeIf } from "../../../util";

describeIf(
  config("HAS_FINEOS_JANUARY_RELEASE") === "true",
  "Create a Max Weekly Benefit Change Notice in FINEOS and check delivery to the LA/Claimant portal",
  {},
  () => {
    after(() => {
      portal.deleteDownloadsFolder();
    });

    const approval = it("Submits a familial caring claim via the API", () => {
      fineos.before();
      cy.task("generateClaim", "CCAP90ER").then((claim) => {
        cy.stash("claim", claim);
        cy.task("submitClaimToAPI", claim).then((response) => {
          if (!response.fineos_absence_id) {
            throw new Error("Response contained no fineos_absence_id property");
          }
          const submission: Submission = {
            application_id: response.application_id,
            fineos_absence_id: response.fineos_absence_id,
            timestamp_from: Date.now(),
          };
          cy.stash("submission", submission);

          const claimPage = fineosPages.ClaimPage.visit(
            submission.fineos_absence_id
          ).adjudicate((adjudication) => {
            adjudication
              .evidence((evidence) => {
                for (const document of claim.documents) {
                  evidence.receive(document.document_type);
                }
              })
              .certificationPeriods((certificationPeriods) =>
                certificationPeriods.prefill()
              )
              .acceptLeavePlan();
          });
          if (config("HAS_APRIL_UPGRADE") === "true") {
            claimPage.approve("Completed", true);
          } else {
            claimPage.approve("Completed", false);
          }
          claimPage.triggerNotice("Designation Notice");
        });
      });
    });

    const notification =
      it("CSR will generate a maximum weekly benefit amount notice", () => {
        cy.dependsOnPreviousPass([approval]);
        fineos.before();
        cy.unstash<Submission>("submission").then(({ fineos_absence_id }) => {
          fineosPages.ClaimPage.visit(fineos_absence_id).paidLeave(
            (paidLeavePage) =>
              paidLeavePage
                .createCorrespondenceDocument(
                  "Maximum Weekly Benefit Change Notice"
                )
                .documents((documentsPage) =>
                  documentsPage
                    .assertDocumentExists(
                      "Maximum Weekly Benefit Change Notice"
                    )
                    .properties(
                      "Maximum Weekly Benefit Change Notice",
                      (propertiesPage) => propertiesPage.setStatus("Completed")
                    )
                    .properties(
                      "Maximum Weekly Benefit Change Notice",
                      (propertiesPage) =>
                        propertiesPage.fileNameShouldMatch(/.pdf$/)
                    )
                )
                .triggerPaidLeaveNotice("Maximum Weekly Benefit Change Notice")
          );
        });
      });

    it("Check the leave admin portal for the max weekly benefit change notice and download it", () => {
      cy.dependsOnPreviousPass([approval, notification]);
      portal.before();
      cy.unstash<Submission>("submission").then((submission) => {
        cy.unstash<DehydratedClaim>("claim").then(({ claim }) => {
          if (!claim.employer_fein) {
            throw new Error("Claim must include employer FEIN");
          }
          const employeeFullName = `${claim.first_name} ${claim.last_name}`;
          portal.loginLeaveAdmin(claim.employer_fein);
          portal.selectClaimFromEmployerDashboard(submission.fineos_absence_id);
          portal.checkNoticeForLeaveAdmin(
            submission.fineos_absence_id,
            employeeFullName,
            "Maximum Weekly Benefit Change Notice (PDF)"
          );
          portal.downloadLegalNotice(submission.fineos_absence_id);
        });
      });
    });

    it("Check the claimant portal for the max weekly benefit change notice and download it", () => {
      cy.dependsOnPreviousPass([approval, notification]);
      portal.before();
      cy.unstash<Submission>("submission").then((submission) => {
        portal.loginClaimant();
        cy.log("Waiting for documents");
        cy.task(
          "waitForClaimDocuments",
          {
            credentials: getClaimantCredentials(),
            application_id: submission.application_id,
            document_type: "Maximum Weekly Benefit Change Notice",
          },
          { timeout: 45000 }
        );
        cy.log("Finished waiting for documents");

        portal.claimantGoToClaimStatus(submission.fineos_absence_id);
        portal.claimantAssertClaimStatus([
          {
            leave: "Care for a Family Member",
            status: "Approved",
          },
        ]);
        cy.findByText("Maximum Weekly Benefit Change Notice (PDF)")
          .should("be.visible")
          .click({ force: true });
        portal.downloadLegalNotice(submission.fineos_absence_id);
      });
    });

    it("Claimant receives max weekly benefit change notification", () => {
      cy.dependsOnPreviousPass([approval, notification]);
      cy.unstash<Submission>("submission").then((submission) => {
        const portalPath = `/applications/status/?absence_case_id=${submission.fineos_absence_id}#view-notices`;
        email
          .getEmails({
            address: "gqzap.notifications@inbox.testmail.app",
            subject: email.getNotificationSubject("appeal (claimant)"),
            messageWildcard: portalPath,
            timestamp_from: submission.timestamp_from,
            debugInfo: { "Fineos Claim ID": submission.fineos_absence_id },
          })
          .then(() => {
            cy.contains("Your maximum weekly benefit has changed");
            cy.get(`a[href$='${portalPath}']`);
          });
      });
    });

    it("Leave admin receives max weekly benefit change notification", () => {
      cy.dependsOnPreviousPass([approval, notification]);
      cy.unstash<Submission>("submission").then((submission) => {
        const portalPath = `/employers/applications/status/?absence_id=${submission.fineos_absence_id}`;
        email
          .getEmails(
            {
              address: "gqzap.notifications@inbox.testmail.app",
              subject: email.getNotificationSubject("appeal (claimant)"),
              messageWildcard: portalPath,
              timestamp_from: submission.timestamp_from,
              debugInfo: { "Fineos Claim ID": submission.fineos_absence_id },
            },
            90000
          )
          .then(() => {
            cy.contains("The applicant’s maximum weekly benefit was changed.");
            cy.get(`a[href*='${portalPath}']`);
          });
      });
    });
  }
);
