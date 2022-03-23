import { fineos, portal, email, fineosPages } from "../../../actions";
import { getClaimantCredentials } from "../../../config";
import { Submission } from "../../../../src/types";
import { config } from "../../../actions/common";

describe("Appeal Hearing Notification & Notice Confirmation", () => {
  after(() => {
    portal.deleteDownloadsFolder();
  });

  const submit = it("Given a fully approved claim", () => {
    fineos.before();
    // Submit a claim via the API, including Employer Response.
    cy.task("generateClaim", "CDENY2ER").then((claim) => {
      cy.stash("claim", claim.claim);
      cy.task("submitClaimToAPI", claim).then((response) => {
        cy.stash("submission", {
          application_id: response.application_id,
          fineos_absence_id: response.fineos_absence_id,
          timestamp_from: Date.now(),
        });

        const claimPage = fineosPages.ClaimPage.visit(
          response.fineos_absence_id
        );
        claimPage.adjudicate((adjudicate) => {
          adjudicate.evidence((evidence) => {
            claim.documents.forEach((document) => {
              evidence.receive(document.document_type);
            });
          });
          adjudicate.certificationPeriods((cert) => cert.prefill());
          adjudicate.acceptLeavePlan();
        });
        claimPage.approve("Approved", config("HAS_APRIL_UPGRADE") === "true");
      });
    });
  });

  const csrAppeal =
    it("CSR will process an appeal and schedule a hearing", () => {
      cy.dependsOnPreviousPass([submit]);
      fineos.before();
      cy.unstash<ApplicationRequestBody>("claim").then((claim) => {
        cy.unstash<Submission>("submission").then(({ fineos_absence_id }) => {
          const claimPage = fineosPages.ClaimPage.visit(fineos_absence_id);
          claimPage.addAppeal(true);
          claimPage.addEmployer(<string>claim.employer_fein);
          claimPage.triggerNotice("SOM Generate Appeals Notice");
          claimPage.appealDocuments((docPage) => {
            docPage.assertDocumentExists("Appeal Acknowledgment");
          });
          claimPage.appealTasks((tasks) => {
            tasks.closeAppealReview();
            tasks.close("Schedule Hearing");
            tasks.close("Conduct Hearing");
            tasks.closeConductHearing();
            tasks.assertTaskExists("Send Decision Notice");
          });
          claimPage.appealDocuments((docPage) => {
            docPage.uploadDocument("Appeal Notice - Claim Decision Changed");
            docPage.assertDocumentUploads(
              "Appeal Notice - Claim Decision Changed"
            );
          });
        });
      });
    });

  it(
    "Should generate an Appeal Acknowledgment that the Leave Admin can view",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass([submit, csrAppeal]);
      portal.before();
      cy.unstash<Submission>("submission").then((submission) => {
        cy.unstash<string>("appeal_case_id").then((appeal_case_id) => {
          cy.unstash<ApplicationRequestBody>("claim").then((claim) => {
            if (!claim.employer_fein) {
              throw new Error("Claim must include employer FEIN");
            }
            const employeeFullName = `${claim.first_name} ${claim.last_name}`;
            portal.loginLeaveAdmin(claim.employer_fein);
            portal.selectClaimFromEmployerDashboard(
              submission.fineos_absence_id
            );
            portal.checkNoticeForLeaveAdmin(
              submission.fineos_absence_id,
              employeeFullName,
              "Appeal Acknowledgment (PDF)"
            );
            portal.downloadLegalNoticeSubcase(appeal_case_id);
          });
        });
      });
    }
  );

  it(
    "Should generate an Appeal Acknowledgment that the Claimant can view",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass([submit, csrAppeal]);
      portal.before();
      portal.loginClaimant();
      cy.unstash<Submission>("submission").then((submission) => {
        cy.unstash<string>("appeal_case_id").then((appeal_case_id) => {
          cy.task(
            "waitForClaimDocuments",
            {
              credentials: getClaimantCredentials(),
              application_id: submission.application_id,
              document_type: "Appeal Acknowledgment",
            },
            { timeout: 30000 }
          );
          portal.claimantGoToClaimStatus(submission.fineos_absence_id);
          cy.findByText("Appeal Acknowledgment (PDF)")
            .should("be.visible")
            .click({ force: true });
          portal.downloadLegalNoticeSubcase(appeal_case_id);
        });
      });
    }
  );

  it("Check appeal notification delivery for Claimant", { retries: 0 }, () => {
    {
      cy.dependsOnPreviousPass([submit, csrAppeal]);
      cy.unstash<Submission>("submission").then((submission) => {
        cy.unstash<ApplicationRequestBody>("claim").then((claim) => {
          const subjectClaimant = email.getNotificationSubject(
            "appeal (claimant)",
            submission.fineos_absence_id,
            `${claim.first_name} ${claim.last_name}`
          );
          email.getEmails(
            {
              address: "gqzap.notifications@inbox.testmail.app",
              subject: subjectClaimant,
              messageWildcard: {
                pattern: `${submission.fineos_absence_id}.*Your appeal has been received`,
              },
              timestamp_from: submission.timestamp_from,
              debugInfo: { "Fineos Claim ID": submission.fineos_absence_id },
            },
            90000
          );
          cy.screenshot("approval-claimant-email");
          cy.contains(submission.fineos_absence_id);
          cy.get(
            `a[href*="/applications/status/?absence_case_id=${submission.fineos_absence_id}#view-notices"]`
          );
        });
      });
    }
  });

  it(
    "Check appeal notification delivery for Leave Admin (employer)",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass([submit, csrAppeal]);
      portal.before();
      cy.unstash<Submission>("submission").then((submission) => {
        cy.unstash<ApplicationRequestBody>("claim").then((claim) => {
          const subjectEmployer = email.getNotificationSubject(
            "appeal (employer)",
            submission.fineos_absence_id,
            `${claim.first_name} ${claim.last_name}`
          );
          email
            .getEmails(
              {
                address: "gqzap.notifications@inbox.testmail.app",
                subject: subjectEmployer,
                messageWildcard: {
                  pattern: `${submission.fineos_absence_id}.*The applicant has filed an appeal`,
                },
                timestamp_from: submission.timestamp_from,
                debugInfo: { "Fineos Claim ID": submission.fineos_absence_id },
              },
              90000
            )
            .then(() => {
              cy.screenshot("approval-leave-admin-email");
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
