import { fineos, portal, email, fineosPages } from "../../../actions";
import { Submission } from "../../../../src/types";
import {
  findCertificationDoc,
  getDocumentReviewTaskName,
} from "../../../../src/util/documents";
import { config } from "../../../actions/common";
import { itIf } from "../../../util";

describe("Approval (notifications/notices)", () => {
  after(() => {
    portal.deleteDownloadsFolder();
  });

  const submission = it("Submits a claim via the API", () => {
    cy.task("generateClaim", "REDUCED_ER").then((claim) => {
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

  it("Submit a fully approved claim", () => {
    cy.dependsOnPreviousPass();
    fineos.before();
    cy.unstash<DehydratedClaim>("claim").then((claim) => {
      cy.unstash<Submission>("submission").then((response) => {
        cy.tryCount().then((tryCount) => {
          if (!response.fineos_absence_id) {
            throw new Error("Response contained no fineos_absence_id property");
          }
          const claimPage = fineosPages.ClaimPage.visit(
            response.fineos_absence_id
          );
          if (tryCount > 0) {
            fineos.assertClaimStatus("Approved");
            claimPage.triggerNotice("Designation Notice");
            return;
          }
          claimPage
            .adjudicate((adjudication) => {
              adjudication
                .evidence((evidence) => {
                  // Receive and approve all of the documentation for the claim.
                  claim.documents.forEach((doc) =>
                    evidence.receive(doc.document_type)
                  );
                })
                .certificationPeriods((cert) => cert.prefill())
                .acceptLeavePlan();
            })
            .tasks((tasks) => {
              const certificationDoc = findCertificationDoc(claim.documents);
              const certificationTask = getDocumentReviewTaskName(
                certificationDoc.document_type
              );
              tasks.assertTaskExists("ID Review");
              tasks.assertTaskExists(certificationTask);
            })
            .shouldHaveStatus("Applicability", "Applicable")
            .shouldHaveStatus("Eligibility", "Met")
            .shouldHaveStatus("Evidence", "Satisfied")
            .shouldHaveStatus("Availability", "Time Available")
            .shouldHaveStatus("Restriction", "Passed")
            .shouldHaveStatus("PlanDecision", "Accepted");
          claimPage.approve("Approved", config("HAS_APRIL_UPGRADE") === "true");
          claimPage.triggerNotice("Designation Notice");
        });
      });
    });
  });

  const cancellation = it("Records Cancellation", () => {
    cy.dependsOnPreviousPass();
    fineos.before();
    cy.unstash<Submission>("submission").then(({ fineos_absence_id }) => {
      fineosPages.ClaimPage.visit(fineos_absence_id)
        .recordCancellation()
        .tasks((tasks) => {
          tasks
            .all()
            .assertTaskExists("Review and Decision Cancel Time Submitted");
        })
        .documents((docsPage) => {
          docsPage.assertDocumentExists("Record Cancel Time");
        })
        .triggerNotice("Leave Cancellation Request");
    });
  });

  it(
    "Check the Leave Admin Portal for the Cancellation notice",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass([submission, cancellation]);
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
            "Approved Time Cancelled (PDF)"
          );
          portal.downloadLegalNotice(submission.fineos_absence_id);
        });
      });
    }
  );

  it(
    "Check the Claimant Portal for the legal notice (Cancellation)",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass([submission, cancellation]);
      portal.before();
      portal.loginClaimant();
      cy.unstash<Submission>("submission").then((submission) => {
        cy.log("Finished waiting for documents");
        portal.claimantGoToClaimStatus(submission.fineos_absence_id);
        portal.claimantAssertClaimStatus([
          {
            leave: "Child Bonding",
            status: "Approved",
          },
        ]);
        cy.findByText("Approved Time Cancelled (PDF)")
          .should("be.visible")
          .click({ force: true });
        portal.downloadLegalNotice(submission.fineos_absence_id);
      });
    }
  );

  itIf(
    config("HAS_FINEOS_JANUARY_RELEASE") === "true",
    "Check the Claimant email for the Cancellation notification.",
    { retries: 0 },
    () => {
      {
        cy.dependsOnPreviousPass([submission, cancellation]);
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
                    pattern: `${submission.fineos_absence_id}.*Your approved time has been cancelled`,
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
                  `a[href$="/applications/status/?absence_case_id=${submission.fineos_absence_id}#view-notices"]`
                );
              });
          });
        });
      }
    }
  );

  itIf(
    config("HAS_FINEOS_JANUARY_RELEASE") === "true",
    "Check the Leave Admin email for the Cancellation notification.",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass([submission, cancellation]);
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
                  pattern: `${submission.fineos_absence_id}.*The applicant’s approved time has been cancelled`,
                },
                timestamp_from: submission.timestamp_from,
                debugInfo: { "Fineos Claim ID": submission.fineos_absence_id },
              },
              90000
            )
            .then(() => {
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
