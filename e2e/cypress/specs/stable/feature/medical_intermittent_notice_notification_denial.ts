import { fineos, portal, email, fineosPages } from "../../../actions";
import { getLeaveAdminCredentials } from "../../../config";
import { Submission } from "../../../../src/types";
import { config } from "../../../actions/common";
import { assertValidClaim } from "../../../../src/util/typeUtils";

describe("Denial Notification and Notice", () => {
  after(() => {
    config("HAS_CLAIMANT_STATUS_PAGE") !== "true" &&
      portal.deleteDownloadsFolder();
  });

  const credentials: Credentials = {
    username: config("PORTAL_USERNAME"),
    password: config("PORTAL_PASSWORD"),
  };

  const submit = it("Given a fully denied claim", () => {
    fineos.before();

    cy.task("generateClaim", "MED_INTER_INEL").then((claim) => {
      cy.task("submitClaimToAPI", {
        ...claim,
        credentials,
      }).then((res) => {
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
      portal.before({
        claimantShowStatusPage: config("HAS_CLAIMANT_STATUS_PAGE") === "true",
      });
      cy.unstash<Submission>("submission").then((submission) => {
        portal.login(credentials);
        cy.visit("/applications");
        if (config("HAS_CLAIMANT_STATUS_PAGE") === "true") {
          portal.claimantGoToClaimStatus(submission.fineos_absence_id);
          // @todo: update status to "Denied" once status page doesn't use static data
          portal.claimantAssertClaimStatus([
            {
              leave: "Serious Health Condition - Employee",
              status: "Denied",
            },
          ]);
          cy.findByText("Denial notice (PDF)").should("be.visible").click();
          // @todo: when application status page uses claim data, assert the documents there
        } else {
          cy.log("Waiting for documents");
          cy.task(
            "waitForClaimDocuments",
            {
              credentials: credentials,
              application_id: submission.application_id,
              document_type: "Denial Notice",
            },
            { timeout: 45000 }
          );
          cy.log("Finished waiting for documents");
          cy.contains("article", submission.fineos_absence_id).within(() => {
            cy.findByText("Denial notice (PDF)").should("be.visible").click();
          });
          portal.downloadLegalNotice(submission.fineos_absence_id);
        }
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
          portal.login(getLeaveAdminCredentials(claim.employer_fein));
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
            employeeFullName,
            "application started",
            submission.fineos_absence_id
          );
          email
            .getEmails(
              {
                address: "gqzap.notifications@inbox.testmail.app",
                subject: subject,
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
            employeeFullName,
            "denial (employer)",
            submission.application_id
          );
          // Check email for Employer/Leave Admin
          email
            .getEmails(
              {
                address: "gqzap.notifications@inbox.testmail.app",
                subject: subjectEmployer,
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
        cy.unstash<ApplicationRequestBody>("claim").then((claim) => {
          const subjectClaimant = email.getNotificationSubject(
            `${claim.first_name} ${claim.last_name}`,
            "denial (claimant)",
            submission.application_id
          );
          // Check email for Claimant/Employee
          email
            .getEmails(
              {
                address: "gqzap.notifications@inbox.testmail.app",
                subject: subjectClaimant,
                messageWildcard: submission.fineos_absence_id,
                timestamp_from: submission.timestamp_from,
                debugInfo: { "Fineos Claim ID": submission.fineos_absence_id },
              },
              // Reduced timeout, since we have multiple tests that run prior to this.
              30000
            )
            .then(() => {
              cy.wait(100);
              cy.contains(submission.fineos_absence_id);
            });
        });
      });
    }
  );
});
