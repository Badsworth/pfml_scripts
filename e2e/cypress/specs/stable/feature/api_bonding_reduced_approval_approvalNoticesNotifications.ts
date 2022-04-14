import { itIf } from "./../../../util";
import { fineos, portal, email, fineosPages } from "../../../actions";
import { getClaimantCredentials } from "../../../config";
import { Submission } from "../../../../src/types";
import { config } from "../../../actions/common";
import {
  findCertificationDoc,
  getDocumentReviewTaskName,
} from "../../../../src/util/documents";
import { DehydratedClaim } from "../../../../src/generation/Claim";
import { isSaturday } from "date-fns";

describe("Approval (notifications/notices)", () => {
  after(() => {
    portal.deleteDownloadsFolder();
  });

  it("Given a submitted claim", () => {
    cy.task("generateClaim", "REDUCED_ER_MIDWEEK").then((claim) => {
      cy.stash("claim", claim);
      cy.task("submitClaimToAPI", claim).then(
        ({ fineos_absence_id, application_id }) => {
          cy.stash("submission", {
            application_id,
            fineos_absence_id,
            timestamp_from: Date.now(),
          });
        }
      );
    });
  });

  const approve = it("Given a fully approved claim", () => {
    cy.dependsOnPreviousPass();
    fineos.before();
    // Submit a claim via the API, including Employer Response.
    cy.unstash<DehydratedClaim>("claim").then((claim) => {
      cy.unstash<Submission>("submission").then(({ fineos_absence_id }) => {
        cy.tryCount().then((tryCount) => {
          const claimPage = fineosPages.ClaimPage.visit(fineos_absence_id);
          if (tryCount > 0) {
            fineos.assertClaimStatus("Approved");
            claimPage
              .triggerNotice("Designation Notice")
              .documents((docPage) =>
                docPage.assertDocumentExists("Approval Notice")
              );
            return;
          }
          claimPage.adjudicate((adjudication) => {
            adjudication.evidence((evidence) => {
              // Receive and approve all of the documentation for the claim.
              claim.documents.forEach((doc) =>
                evidence.receive(doc.document_type)
              );
            });
            adjudication.certificationPeriods((cert) => cert.prefill());
            adjudication.acceptLeavePlan();
          });
          claimPage.tasks((tasks) => {
            const certificationDoc = findCertificationDoc(claim.documents);
            const certificationTask = getDocumentReviewTaskName(
              certificationDoc.document_type
            );
            tasks.assertTaskExists("ID Review");
            tasks.assertTaskExists(certificationTask);
          });
          claimPage.shouldHaveStatus("Applicability", "Applicable");
          claimPage.shouldHaveStatus("Eligibility", "Met");
          claimPage.shouldHaveStatus("Evidence", "Satisfied");
          claimPage.shouldHaveStatus("Availability", "Time Available");
          claimPage.shouldHaveStatus("Restriction", "Passed");
          claimPage.shouldHaveStatus("PlanDecision", "Accepted");
          claimPage.approve("Approved", config("HAS_APRIL_UPGRADE") === "true");
          claimPage
            .triggerNotice("Designation Notice")
            .documents((docPage) =>
              docPage.assertDocumentExists("Approval Notice")
            );
        });
      });
    });
  });

  itIf(
    config("HAS_APRIL_UPGRADE") === "true",
    "Payments are scheduled for Sundays even though claim doesn't start on a Sunday",
    {},
    () => {
      cy.dependsOnPreviousPass();
      fineos.before();
      cy.unstash<Submission>("submission").then(({ fineos_absence_id }) => {
        fineosPages.ClaimPage.visit(fineos_absence_id).paidLeave(
          (paidLeavePage) => {
            paidLeavePage.getAmountsPending().then((records) => {
              const processingDates = records.reduce<Date[]>((acc, record) => {
                acc.push(new Date(record.processingDate));
                return acc;
              }, []);
              expect(processingDates.every((val) => isSaturday(val))).equal(
                true,
                "Payments are scheduled for Saturday"
              );
            });
          }
        );
      });
    }
  );

  it(
    "Should generate a legal notice (Approval) that the claimant can view",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass([approve]);
      portal.before();
      portal.loginClaimant();
      cy.unstash<Submission>("submission").then((submission) => {
        // Wait for the legal document to arrive.
        cy.task(
          "waitForClaimDocuments",
          {
            credentials: getClaimantCredentials(),
            application_id: submission.application_id,
            document_type: "Approval Notice",
          },
          { timeout: 30000 }
        );
        portal.claimantGoToClaimStatus(submission.fineos_absence_id);
        portal.claimantAssertClaimStatus([
          { leave: "Child Bonding", status: "Approved" },
        ]);
        cy.findByText("Approval notice (PDF)", { timeout: 20000 })
          .should("be.visible")
          .click({ force: true });
        portal.downloadLegalNotice(submission.fineos_absence_id);
      });
    }
  );

  it(
    "Should generate a legal notice (Approval) that the Leave Administrator can view",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass([approve]);
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
            "Approval notice (PDF)"
          );
          portal.downloadLegalNotice(submission.fineos_absence_id);
        });
      });
    }
  );

  it(
    "Should generate a 'Action Required' ER notification for the Leave Administrator",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass([approve]);
      cy.unstash<Submission>("submission").then((submission) => {
        email
          .getEmails({
            address: "gqzap.notifications@inbox.testmail.app",
            subjectWildcard: `Action required: Respond to *'s paid leave application`,
            messageWildcard: submission.fineos_absence_id,
            timestamp_from: submission.timestamp_from,
            debugInfo: { "Fineos Claim ID": submission.fineos_absence_id },
          })
          .then(() => {
            cy.get(
              `a[href*="/employers/applications/new-application/?absence_id=${submission.fineos_absence_id}"]`
            );
          });
      });
    }
  );

  it(
    "Should generate an approval notification for the Leave Administrator",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass([approve]);
      cy.unstash<Submission>("submission").then((submission) => {
        cy.unstash<DehydratedClaim>("claim").then(({ claim }) => {
          const subjectEmployer = email.getNotificationSubject(
            "approval (employer)",
            submission.fineos_absence_id
          );
          // Check email for Employer/Leave Admin
          email
            .getEmails(
              {
                address: "gqzap.notifications@inbox.testmail.app",
                subjectWildcard: subjectEmployer,
                messageWildcard: submission.fineos_absence_id,
                timestamp_from: submission.timestamp_from,
                debugInfo: { "Fineos Claim ID": submission.fineos_absence_id },
              },
              90000
            )
            .then(() => {
              const dob =
                claim.date_of_birth?.replace(/-/g, "/").slice(5) + "/****";
              cy.log("DOB", dob);
              cy.contains(dob);
              cy.contains(`${claim.first_name} ${claim.last_name}`);
              cy.contains(submission.fineos_absence_id);
              cy.get(
                `a[href*="/employers/applications/status/?absence_id=${submission.fineos_absence_id}"]`
              );
            });
        });
      });
    }
  );

  it(
    "Should generate an approval notification for the claimant",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass([approve]);
      cy.unstash<Submission>("submission").then((submission) => {
        const subjectClaimant = email.getNotificationSubject(
          "approval (claimant)",
          submission.fineos_absence_id
        );
        // Check email for Claimant/Employee
        email.getEmails({
          address: "gqzap.notifications@inbox.testmail.app",
          subject: subjectClaimant,
          messageWildcard: submission.fineos_absence_id,
          timestamp_from: submission.timestamp_from,
          debugInfo: { "Fineos Claim ID": submission.fineos_absence_id },
        });
        cy.contains(submission.fineos_absence_id);
        cy.get(`a[href*="${config("PORTAL_BASEURL")}/applications"]`);
      });
    }
  );
});
