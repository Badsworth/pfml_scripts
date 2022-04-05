import { fineos, fineosPages, portal, email } from "../../../actions";
import { Submission } from "../../../../src/types";
import { getClaimantCredentials } from "../../../config";
import { config } from "../../../actions/common";
import { itIf } from "../../../util";

// @TODO parts of this test is only available in certain environments with the FINEOS
// @TODO January release and the email template updates.

describe("Post-approval (notifications/notices)", () => {
  const APRIL_UPGRADE: boolean = config("HAS_APRIL_UPGRADE") === "true";
  after(() => {
    portal.deleteDownloadsFolder();
  });

  it("Submits a claim via the API", () => {
    cy.task("generateClaim", "CHAP_ER").then((claim) => {
      cy.task("submitClaimToAPI", claim).then((res) => {
        cy.stash("claim", claim);
        cy.stash("submission", {
          application_id: res.application_id,
          fineos_absence_id: res.fineos_absence_id,
          timestamp_from: Date.now(),
        });
      });
    });
  });

  const approval = it("CSR rep approves caring leave claim", () => {
    cy.dependsOnPreviousPass();
    fineos.before();
    cy.unstash<DehydratedClaim>("claim").then((claim) => {
      cy.unstash<Submission>("submission").then((response) => {
        cy.tryCount().then((tryCount) => {
          if (!response.fineos_absence_id) {
            throw new Error("Response contained no fineos_absence_id property");
          }
          // Approve the claim
          const claimPage = fineosPages.ClaimPage.visit(
            response.fineos_absence_id
          );
          if (tryCount > 0) {
            fineos.assertClaimStatus("Approved");
            claimPage.triggerNotice("Designation Notice");
            return;
          }
          claimPage.triggerNotice("Preliminary Designation");
          fineos.onTab("Absence Hub");
          claimPage.adjudicate((adjudication) => {
            adjudication
              .evidence((evidence) => {
                claim.documents.forEach((doc) =>
                  evidence.receive(doc.document_type)
                );
              })
              .certificationPeriods((cert) => cert.prefill())
              .acceptLeavePlan();
          });
          // Skip checking tasks. We do that in other tests.
          // Also skip checking claim status for the same reason.
          claimPage.approve("Approved", config("HAS_APRIL_UPGRADE") === "true");
          claimPage.triggerNotice("Designation Notice");
        });
      });
    });
  });

  const denyModification =
    it('Generates a "Change Request Denial" document when deny an approved claim in review', () => {
      cy.dependsOnPreviousPass([approval]);
      fineos.before();
      cy.unstash<Submission>("submission").then((submission) => {
        //visit claim after approval to put in review and deny.
        const claimPage = fineosPages.ClaimPage.visit(
          submission.fineos_absence_id
        );
        claimPage
          .leaveDetails((leaveDetails) => {
            const adjudication = leaveDetails.inReview(APRIL_UPGRADE);
            if (APRIL_UPGRADE) {
              adjudication.rejectLeavePlan().clickOK();
            }
            adjudication.doNothing();
          })
          .denyExtendedTime("Claimant/Family member deceased", APRIL_UPGRADE)
          .triggerNotice("Review Denial Notice")
          .documents((docPage) =>
            docPage.assertDocumentExists("Change Request Denied")
          );
      });
    });

  it(
    "Check the Claimant Portal status and for the legal notice Change Request Denied or Denial Notice",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass([denyModification]);
      portal.before();
      cy.unstash<Submission>("submission").then((submission) => {
        portal.loginClaimant();
        cy.log("Waiting for documents");
        cy.task(
          "waitForClaimDocuments",
          {
            credentials: getClaimantCredentials(),
            application_id: submission.application_id,
            document_type: "Change Request Denied",
          },
          { timeout: 45000 }
        );
        cy.log("Finished waiting for documents");
        portal.claimantGoToClaimStatus(submission.fineos_absence_id);
        portal.claimantAssertClaimStatus([
          {
            leave: "Care for a Family Member",
            status: "Denied",
          },
        ]);
        //@TODO this will need to be adjusted for the January release for FINEOS version
        // If the environment has the January release add to the if statement
        if (config("HAS_FINEOS_JANUARY_RELEASE") === "true") {
          cy.findByText("Change Request Denied (PDF)")
            .should("be.visible")
            .click({ force: true });
          portal.downloadLegalNotice(submission.fineos_absence_id);
        } else {
          // Any other FINEOS version from Dec or before will need to use the else statement
          cy.findByText("Approval notice (PDF)")
            .should("be.visible")
            .click({ force: true });
          portal.downloadLegalNotice(submission.fineos_absence_id);
        }
      });
    }
  );

  const hasJanuaryRelease = config("HAS_FINEOS_JANUARY_RELEASE") === "true";
  itIf(
    hasJanuaryRelease,
    "Check the Leave Admin Portal for the Change Request Denied notice",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass([denyModification]);
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
            "Change Request Denied (PDF)"
          );
          portal.downloadLegalNotice(submission.fineos_absence_id);
        });
      });
    }
  );

  itIf(
    hasJanuaryRelease,
    "Check the Claimant email for the Change Request Denial notification.",
    { retries: 0 },
    () => {
      {
        cy.dependsOnPreviousPass([denyModification]);
        cy.unstash<Submission>("submission").then((submission) => {
          cy.unstash<ApplicationRequestBody>("claim").then((claim) => {
            // The notification is using the same subject line as Appeals claimant.
            const subjectClaimant = email.getNotificationSubject(
              "appeal (claimant)",
              submission.fineos_absence_id,
              `${claim.first_name} ${claim.last_name}`
            );
            email
              .getEmails(
                {
                  address: "gqzap.notifications@inbox.testmail.app",
                  subject: subjectClaimant,
                  messageWildcard: {
                    pattern: `${submission.fineos_absence_id}.*Your change request has been denied`,
                  },
                  timestamp_from: submission.timestamp_from,
                  debugInfo: {
                    "Fineos Claim ID": submission.fineos_absence_id,
                  },
                },
                90000
              )
              .then(() => {
                cy.screenshot("Claimant email");
                cy.contains(submission.fineos_absence_id);
              });
          });
        });
      }
    }
  );

  itIf(
    hasJanuaryRelease,
    "Check the Leave Admin email for the Change Request Denial notification.",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass([denyModification]);
      cy.unstash<Submission>("submission").then((submission) => {
        cy.unstash<ApplicationRequestBody>("claim").then((claim) => {
          // The notification is using the same subject line as Appeals claimant.
          const subjectEmployer = email.getNotificationSubject(
            "appeal (claimant)",
            submission.fineos_absence_id,
            `${claim.first_name} ${claim.last_name}`
          );
          email
            .getEmails(
              {
                address: "gqzap.notifications@inbox.testmail.app",
                subject: subjectEmployer,
                // Had to adjust the messageWildcard to use line for Leave Admin only.
                // Was getting a duplicate Claimant emails or not found because of to many notifications.
                messageWildcard: {
                  pattern: `${submission.fineos_absence_id}.*The applicant’s change request has been denied.`,
                },
                timestamp_from: submission.timestamp_from,
                debugInfo: {
                  "Fineos Claim ID": submission.fineos_absence_id,
                },
              },
              90000
            )
            .then(() => {
              cy.screenshot("Leave Admin email");
              cy.contains(submission.fineos_absence_id);
              cy.get(
                `a[href*="/employers/applications/status/?absence_id=${submission.fineos_absence_id}"]`
              );
            });
        });
      });
    }
  );
});
