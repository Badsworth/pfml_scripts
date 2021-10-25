import { fineos, portal, email, fineosPages } from "../../../actions";
import { Submission } from "../../../../src/types";
import { assertValidClaim } from "../../../../src/util/typeUtils";
import { getClaimantCredentials } from "../../../config";

describe("Denial Notification and Notice", () => {
  after(() => {
    portal.deleteDownloadsFolder();
  });

  const submit = it("Given a fully denied claim", () => {
    fineos.before();

    cy.task("generateClaim", "MED_INTER_INEL").then((claim) => {
      cy.task("submitClaimToAPI", claim).then((res) => {
        cy.stash("claim", claim.claim);
        cy.stash("submission", {
          application_id: res.application_id,
          fineos_absence_id: res.fineos_absence_id,
          timestamp_from: Date.now(),
        });

        fineosPages.ClaimPage.visit(res.fineos_absence_id)
          .shouldHaveStatus("Eligibility", "Not Met")
          .deny("Claimant wages failed 30x rule")
          .triggerNotice("Leave Request Declined")
          .triggerNotice("Preliminary Designation")
          .documents((docPage) =>
            docPage.assertDocumentExists("Denial Notice")
          );
      });
    });
  });

  it(
    "Should generate a legal notice (Denial) that the claimant can view",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass([submit]);
      portal.before();
      cy.unstash<Submission>("submission").then((submission) => {
        portal.loginClaimant();
        cy.log("Waiting for documents");
        cy.task(
          "waitForClaimDocuments",
          {
            credentials: getClaimantCredentials(),
            application_id: submission.application_id,
            document_type: "Denial Notice",
          },
          { timeout: 45000 }
        );
        cy.log("Finished waiting for documents");
        portal.claimantGoToClaimStatus(submission.fineos_absence_id);
        portal.claimantAssertClaimStatus([
          {
            leave: "Serious Health Condition - Employee",
            status: "Denied",
          },
        ]);
        cy.findByText("Denial notice (PDF)")
          .should("be.visible")
          .click({ force: true });
        portal.downloadLegalNotice(submission.fineos_absence_id);
      });
    }
  );

  it(
    "Should generate a legal notice (Denial) that the Leave Administrator can view",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass([submit]);
      portal.before();
      cy.visit("/");
      cy.unstash<Submission>("submission").then((submission) => {
        cy.unstash<ApplicationRequestBody>("claim").then((claim) => {
          assertValidClaim(claim);
          const employeeFullName = `${claim.first_name} ${claim.last_name}`;
          portal.loginLeaveAdmin(claim.employer_fein);
          portal.selectClaimFromEmployerDashboard(submission.fineos_absence_id);
          portal.checkNoticeForLeaveAdmin(
            submission.fineos_absence_id,
            employeeFullName,
            "denial"
          );
          portal.downloadLegalNotice(submission.fineos_absence_id);
        });
      });
    }
  );

  it(
    "I should receive an 'application started' notification (employer)",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass([submit]);
      cy.unstash<ApplicationRequestBody>("claim").then((claim) => {
        cy.unstash<Submission>("submission").then((submission) => {
          const employeeFullName = `${claim.first_name} ${claim.last_name}`;
          const subject = email.getNotificationSubject(
            "application started",
            submission.fineos_absence_id
          );
          email
            .getEmails(
              {
                address: "gqzap.notifications@inbox.testmail.app",
                subjectWildcard: subject,
                timestamp_from: submission.timestamp_from,
                messageWildcard: submission.fineos_absence_id,
                debugInfo: { "Fineos Claim ID": submission.fineos_absence_id },
              },
              45000
            )
            .then(() => {
              const dob =
                claim.date_of_birth?.replace(/-/g, "/").slice(5) + "/****";
              cy.log(dob);
              cy.contains(dob);
              cy.contains(employeeFullName);
              cy.contains(dob);
              cy.contains(submission.fineos_absence_id);
            });
        });
      });
    }
  );

  it(
    "Should generate a (Denial) notification for the Leave Administrator",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass([submit]);
      cy.unstash<Submission>("submission").then((submission) => {
        cy.unstash<ApplicationRequestBody>("claim").then((claim) => {
          const employeeFullName = `${claim.first_name} ${claim.last_name}`;
          const subjectEmployer = email.getNotificationSubject(
            "denial (employer)",
            submission.application_id
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
              // Reduced timeout, since we have multiple tests that run prior to this.
              30000
            )
            .then(() => {
              const dob =
                claim.date_of_birth?.replace(/-/g, "/").slice(5) + "/****";
              cy.log("DOB", dob);
              cy.contains(dob);
              cy.contains(employeeFullName);
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
    "Should generate a (Denial) notification for the claimant",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass([submit]);
      cy.unstash<Submission>("submission").then((submission) => {
        const subjectClaimant = email.getNotificationSubject(
          "denial (claimant)",
          submission.application_id
        );
        // Check email for Claimant/Employee
        email
          .getEmails(
            {
              address: "gqzap.notifications@inbox.testmail.app",
              subjectWildcard: subjectClaimant,
              messageWildcard: submission.fineos_absence_id,
              timestamp_from: submission.timestamp_from,
              debugInfo: { "Fineos Claim ID": submission.fineos_absence_id },
            },
            // Reduced timeout, since we have multiple tests that run prior to this.
            30000
          )
          .then(() => {
            cy.contains(submission.fineos_absence_id);
          });
      });
    }
  );
});
