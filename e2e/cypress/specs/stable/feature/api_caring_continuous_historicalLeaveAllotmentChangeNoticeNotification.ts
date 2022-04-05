import { fineos, fineosPages, portal, email } from "../../../actions";
import { Submission } from "../../../../src/types";
import { getClaimantCredentials } from "../../../config";
import { describeIf } from "../../../util";
import { config } from "../../../actions/common";

describeIf(
  config("HAS_FINEOS_JANUARY_RELEASE") === "true",
  "Create a new caring leave claim in API submission and add Historical Absence case",
  {},
  () => {
    before(() => {
      portal.deleteDownloadsFolder();
    });

    const historical =
      it("Create historical absence case within Absence Case", () => {
        fineos.before();
        cy.task("generateClaim", "HIST_CASE").then((claim) => {
          cy.task("submitClaimToAPI", claim).then((response) => {
            cy.stash("claim", claim.claim);
            cy.stash("submission", {
              application_id: response.application_id,
              fineos_absence_id: response.fineos_absence_id,
              timestamp_from: Date.now(),
            });
            fineosPages.ClaimPage.visit(
              response.fineos_absence_id
            ).addHistoricalAbsenceCase(config("HAS_APRIL_UPGRADE") === "true");
            const claimPage = fineosPages.ClaimPage.visit(
              response.fineos_absence_id
            ).adjudicate((adjudication) => {
              adjudication
                .evidence((evidence) => {
                  claim.documents.forEach((doc) =>
                    evidence.receive(doc.document_type)
                  );
                })
                .certificationPeriods((cert) => cert.prefill())
                .acceptLeavePlan();
            });
            claimPage.approve(
              "Approved",
              config("HAS_APRIL_UPGRADE") === "true"
            );
            claimPage.triggerNotice("Designation Notice");
          });
        });
      });

    const leaveallotment =
      it("Adding the Leave Allotment Change Notice and trigger the notice", () => {
        cy.dependsOnPreviousPass([historical]);
        fineos.before();
        cy.unstash<Submission>("submission").then((submission) => {
          const claimPage = fineosPages.ClaimPage.visit(
            submission.fineos_absence_id
          );
          // @todo Rename this to addCorrespondence and add variable for notices.
          claimPage.addLeaveAllotmentChangeNotice();
          claimPage.documents((docs) => {
            docs.assertDocumentExists("Leave Allotment Change Notice");
            docs.adjustDocumentStatus(
              "Leave Allotment Change Notice",
              "Completed"
            );
            docs.checkDocumentFileExtension(
              "Leave Allotment Change Notice",
              /\.pdf$/
            );
          });
          claimPage.triggerNotice("Leave Allotment Change Notice");
        });
      });

    it(
      "Check the Claimant Portal for the legal notice (Leave Allotment Change)",
      { retries: 0 },
      () => {
        cy.dependsOnPreviousPass([historical, leaveallotment]);
        portal.before();
        portal.loginClaimant();
        cy.unstash<Submission>("submission").then((submission) => {
          cy.task(
            "waitForClaimDocuments",
            {
              credentials: getClaimantCredentials(),
              application_id: submission.application_id,
              document_type: "Leave Allotment Change Notice",
            },
            { timeout: 30000 }
          );
          portal.claimantGoToClaimStatus(submission.fineos_absence_id);
          cy.findByText("Leave Allotment Change Notice (PDF)")
            .should("be.visible")
            .click({ force: true });
          portal.downloadLegalNotice(submission.fineos_absence_id);
        });
      }
    );

    it(
      "Check the Leave Admin Portal for the legal notice (Leave Allotment Change)",
      { retries: 0 },
      () => {
        cy.dependsOnPreviousPass([historical, leaveallotment]);
        portal.before();
        cy.unstash<Submission>("submission").then((submission) => {
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
              "Leave Allotment Change Notice (PDF)"
            );
            portal.downloadLegalNotice(submission.fineos_absence_id);
          });
        });
      }
    );

    it(
      "Check the Claimant email for the Leave Allotment Change notification",
      { retries: 0 },
      () => {
        cy.dependsOnPreviousPass([historical, leaveallotment]);
        cy.unstash<Submission>("submission").then((submission) => {
          cy.unstash<ApplicationRequestBody>("claim").then((claim) => {
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
                    pattern: `${submission.fineos_absence_id}.*Your maximum leave allotment has changed`,
                  },
                  timestamp_from: submission.timestamp_from,
                  debugInfo: {
                    "Fineos Claim ID": submission.fineos_absence_id,
                  },
                },
                75000
              )
              .then(() => {
                cy.get(
                  `a[href$="/applications/status/?absence_case_id=${submission.fineos_absence_id}#view-notices"]`
                );
              });
          });
        });
      }
    );

    it(
      "Check the Leave Admin email for the Leave Allotment Change notification",
      { retries: 0 },
      () => {
        cy.dependsOnPreviousPass([historical, leaveallotment]);
        cy.unstash<Submission>("submission").then((submission) => {
          cy.unstash<ApplicationRequestBody>("claim").then((claim) => {
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
                    pattern: `${submission.fineos_absence_id}.*The applicant’s leave allotment was changed`,
                  },
                  timestamp_from: submission.timestamp_from,
                  debugInfo: {
                    "Fineos Claim ID": submission.fineos_absence_id,
                  },
                },
                90000
              )
              .then(() => {
                cy.get(
                  `a[href*="/employers/applications/status/?absence_id=${submission.fineos_absence_id}"]`
                );
              });
          });
        });
      }
    );
  }
);
