import { fineos, fineosPages, email, portal } from "../../../actions";
import { Submission } from "../../../../src/types";
import { getClaimantCredentials } from "../../../config";
import { config } from "../../../actions/common";

describe("Change request approval (notifications/notices)", () => {
  const APRIL_UPGRADE: boolean = config("HAS_APRIL_UPGRADE") === "true";

  after(() => {
    portal.deleteDownloadsFolder();
  });

  const approval =
    it("Submit a Care for a Family member claim for approval", () => {
      fineos.before();
      //Submit a claim via the API, including Employer Response.
      cy.task("generateClaim", "MED_LSDCR").then((claim) => {
        cy.stash("claim", claim);
        cy.task("submitClaimToAPI", claim).then((response) => {
          const submission: Submission = {
            application_id: response.application_id,
            fineos_absence_id: response.fineos_absence_id,
            timestamp_from: Date.now(),
          };

          cy.stash("submission", submission);
          // Approve the claim
          const claimPage = fineosPages.ClaimPage.visit(
            response.fineos_absence_id
          );
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
          claimPage.approve("Approved", config("HAS_APRIL_UPGRADE") === "true");
          claimPage.triggerNotice("Designation Notice");
        });
      });
    });
  const approveModification =
    it('Generates a "Change Request Approval" document when approving an already approved claim in review', () => {
      cy.dependsOnPreviousPass([approval]);
      fineos.before();
      cy.unstash<Submission>("submission").then((submission) => {
        //visit claim after approval to put in review and deny.
        const claimPage = fineosPages.ClaimPage.visit(
          submission.fineos_absence_id
        );
        claimPage.leaveDetails((leaveDetails) => {
          const adjudication = leaveDetails.inReview(APRIL_UPGRADE);
          if (APRIL_UPGRADE) {
            adjudication.acceptLeavePlan().clickOK();
          }
          adjudication.doNothing();
        });
        APRIL_UPGRADE
          ? claimPage.approve("Approved", true)
          : claimPage.approveExtendedTime();
        claimPage
          .triggerNotice("Review Approval Notice")
          .documents((docPage) =>
            docPage.assertDocumentExists("Change Request Approved")
          );
      });
    });
  it(
    "Check the Leave Admin Portal for the Change Request Approved notice",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass([approveModification]);
      portal.before();
      cy.unstash<Submission>("submission").then((submission) => {
        cy.unstash<DehydratedClaim>("claim").then((claim) => {
          const employeeFullName = `${claim.claim.first_name} ${claim.claim.last_name}`;
          portal.loginLeaveAdmin(<string>claim.claim.employer_fein);
          portal.selectClaimFromEmployerDashboard(submission.fineos_absence_id);
          portal.checkNoticeForLeaveAdmin(
            submission.fineos_absence_id,
            employeeFullName,
            "Change Request Approved (PDF)"
          );
          portal.downloadLegalNotice(submission.fineos_absence_id);
        });
      });
    }
  );
  it(
    "Check the Claimant Portal for the legal notice (Change Request Approved)",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass([approveModification]);
      portal.before();
      cy.unstash<Submission>("submission").then((submission) => {
        portal.loginClaimant();
        cy.log("Waiting for documents");
        cy.task(
          "waitForClaimDocuments",
          {
            credentials: getClaimantCredentials(),
            application_id: submission.application_id,
            document_type: "Change Request Approved",
          },
          { timeout: 45000 }
        );
        cy.log("Finished waiting for documents");
        portal.claimantGoToClaimStatus(submission.fineos_absence_id);
        portal.claimantAssertClaimStatus([
          {
            leave: "Serious Health Condition - Employee",
            status: "Approved",
          },
        ]);
        cy.findByText("Change Request Approved (PDF)")
          .should("be.visible")
          .click({ force: true });
        portal.downloadLegalNotice(submission.fineos_absence_id);
      });
    }
  );
  it(
    "Check the Claimant email for the Change Request Approved notification",
    { retries: 0 },
    () => {
      {
        cy.dependsOnPreviousPass([approveModification]);
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
                    pattern: `${submission.fineos_absence_id}.*Your change request has been approved`,
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
                cy.get(
                  `a[href$="/applications/status/?absence_case_id=${submission.fineos_absence_id}#view-notices"]`
                );
              });
          });
        });
      }
    }
  );
  it(
    "Check the Leave Admin email for the Change Request Approved notification",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass([approveModification]);
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
                messageWildcard: {
                  pattern: `${submission.fineos_absence_id}.*The applicant’s change request has been approved`,
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
              cy.get(
                `a[href*="/employers/applications/status/?absence_id=${submission.fineos_absence_id}"]`
              );
            });
        });
      });
    }
  );
});
