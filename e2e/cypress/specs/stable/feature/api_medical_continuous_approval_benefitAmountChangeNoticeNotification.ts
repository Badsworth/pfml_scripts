import { email, fineos, fineosPages, portal } from "../../../actions";
import { Submission } from "../../../../src/types";
import { getClaimantCredentials } from "../../../config";
import { config } from "../../../actions/common";

describe(
  "Create a Benefit Amount Change Notice in FINEOS and check delivery to the LA/Claimant portal",
  {},
  () => {
    after(() => {
      portal.deleteDownloadsFolder();
    });

    const submission = it("Submits a child bonding claim via the API", () => {
      cy.task("generateClaim", "BHAP1ER").then((claim) => {
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
        });
      });
    });

    const approval = it("Approves the child bonding claim", () => {
      fineos.before();
      cy.unstash<DehydratedClaim>("claim").then((claim) => {
        cy.unstash<Submission>("submission").then((submission) => {
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
          claimPage.approve("Approved", config("HAS_APRIL_UPGRADE") === "true");
          claimPage.triggerNotice("Designation Notice");
        });
      });
    });

    const notification =
      it("Generates 'Benefit Amount Change Notice' document and triggers notification", () => {
        cy.dependsOnPreviousPass([submission, approval]);
        fineos.before();
        cy.unstash<Submission>("submission").then((submission) => {
          fineosPages.ClaimPage.visit(submission.fineos_absence_id).paidLeave(
            (paidLeavePage) => {
              paidLeavePage
                .createCorrespondenceDocument("Benefit Amount Change Notice")
                .documents((documentsPage) =>
                  documentsPage
                    .assertDocumentExists("Benefit Amount Change Notice")
                    .properties(
                      "Benefit Amount Change Notice",
                      (propertiesPage) => propertiesPage.setStatus("Completed")
                    )
                    .properties(
                      "Benefit Amount Change Notice",
                      (propertiesPage) =>
                        propertiesPage.fileNameShouldMatch(/\.pdf$/)
                    )
                )
                .triggerPaidLeaveNotice("Benefit Amount Change Notice");
            }
          );
        });
      });

    it("Check the Leave Admin Portal for the Benefit Amount Change Notice and download it", () => {
      cy.dependsOnPreviousPass([submission, approval, notification]);
      portal.before();
      cy.unstash<Submission>("submission").then((submission) => {
        cy.unstash<DehydratedClaim>("claim").then((claim) => {
          if (!claim.claim.employer_fein) {
            throw new Error("Claim must include employer FEIN");
          }
          const employeeFullName = `${claim.claim.first_name} ${claim.claim.last_name}`;
          portal.loginLeaveAdmin(claim.claim.employer_fein);
          portal.selectClaimFromEmployerDashboard(submission.fineos_absence_id);
          portal.checkNoticeForLeaveAdmin(
            submission.fineos_absence_id,
            employeeFullName,
            "Benefit Amount Change Notice (PDF)"
          );
          portal.downloadLegalNotice(submission.fineos_absence_id);
        });
      });
    });

    it("Check the Claimant Portal for the Benefit Amount Change Notice and download it", () => {
      cy.dependsOnPreviousPass([submission, approval, notification]);
      portal.before();
      cy.unstash<Submission>("submission").then((submission) => {
        portal.loginClaimant();
        cy.log("Waiting for documents");
        cy.task(
          "waitForClaimDocuments",
          {
            credentials: getClaimantCredentials(),
            application_id: submission.application_id,
            document_type: "Benefit Amount Change Notice",
          },
          { timeout: 45000 }
        );
        cy.log("Finished waiting for documents");
        portal.claimantGoToClaimStatus(submission.fineos_absence_id);
        portal.claimantAssertClaimStatus([
          {
            leave: "Child Bonding",
            status: "Approved",
          },
        ]);
        cy.findByText("Benefit Amount Change Notice (PDF)")
          .should("be.visible")
          .click({ force: true });
        portal.downloadLegalNotice(submission.fineos_absence_id);
      });
    });

    it("Employee receives notification for Benefit Amount Change", () => {
      cy.dependsOnPreviousPass([submission, approval, notification]);
      cy.unstash<Submission>("submission").then((submission) => {
        const portalPath = `/applications/status/?absence_case_id=${submission.fineos_absence_id}#view-notices`;
        email
          .getEmails(
            {
              address: "gqzap.notifications@inbox.testmail.app",
              // this email uses the same subject as claimaint appeals
              subject: email.getNotificationSubject("appeal (claimant)"),
              messageWildcard: portalPath,
              timestamp_from: submission.timestamp_from,
              debugInfo: { "Fineos Claim ID": submission.fineos_absence_id },
            },
            90000
          )
          .then(() => {
            cy.contains("Your benefit amount has changed.");
            cy.get(`a[href*='${portalPath}']`);
          });
      });
    });

    it("Employer receives notification for Benefit Amount Change", () => {
      cy.dependsOnPreviousPass([submission, approval, notification]);
      cy.unstash<Submission>("submission").then((submission) => {
        const portalPath = `/employers/applications/status/?absence_id=${submission.fineos_absence_id}`;
        email
          .getEmails(
            {
              address: "gqzap.notifications@inbox.testmail.app",
              // this email uses the same subject as claimaint appeals
              subject: email.getNotificationSubject("appeal (claimant)"),
              messageWildcard: portalPath,
              timestamp_from: submission.timestamp_from,
              debugInfo: { "Fineos Claim ID": submission.fineos_absence_id },
            },
            90000
          )
          .then(() => {
            cy.contains("The applicant’s benefit amount was changed.");
            cy.get(`a[href*='${portalPath}']`);
          });
      });
    });
  }
);
