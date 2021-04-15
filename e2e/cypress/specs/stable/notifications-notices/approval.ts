import { fineos, portal, email } from "../../../tests/common/actions";
import { beforeFineos } from "../../../tests/common/before";
import { beforePortal } from "../../../tests/common/before";
import { getFineosBaseUrl, getLeaveAdminCredentials } from "../../../config";
import { Submission } from "../../../../src/types";
import { getEmails } from "../../../tests/common/actions/email";

describe("Approval (notifications/notices)", () => {
  const credentials: Credentials = {
    username: Cypress.env("E2E_PORTAL_USERNAME"),
    password: Cypress.env("E2E_PORTAL_PASSWORD"),
  };

  const submit = it(
    "Given a fully approved claim",
    { baseUrl: getFineosBaseUrl() },
    () => {
      beforeFineos();
      cy.visit("/");
      // Submit a claim via the API, including Employer Response.
      cy.task("generateClaim", "BHAP1ER").then((claim) => {
        cy.stash("claim", claim.claim);
        cy.task("submitClaimToAPI", {
          ...claim,
          credentials,
        }).then((response) => {
          if (!response.fineos_absence_id) {
            throw new Error("Response contained no fineos_absence_id property");
          }

          cy.stash("submission", {
            application_id: response.application_id,
            fineos_absence_id: response.fineos_absence_id,
            timestamp_from: Date.now(),
          });
          fineos.claimAdjudicationFlow(response.fineos_absence_id, true);
          fineos.triggerNoticeRelease("Approval Notice");
        });
      });
    }
  );

  it(
    "Should generate a legal notice that the claimant can view",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass([submit]);
      beforePortal();
      cy.visit("/");
      portal.login(credentials);
      cy.unstash<Submission>("submission").then((submission) => {
        // Wait for the legal document to arrive.
        cy.task(
          "waitForClaimDocuments",
          {
            credentials: credentials,
            application_id: submission.application_id,
            document_type: "Approval Notice",
          },
          { timeout: 30000 }
        );

        cy.visit("/applications");
        cy.contains("article", submission.fineos_absence_id).within(() => {
          cy.contains("a", "Approval notice").should("be.visible");
        });
      });
    }
  );

  it(
    "Should generate a legal notice that the Leave Administrator can view",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass([submit]);
      beforePortal();
      cy.visit("/");
      cy.unstash<Submission>("submission").then((submission) => {
        cy.unstash<ApplicationRequestBody>("claim").then((claim) => {
          if (!claim.employer_fein) {
            throw new Error("Claim must include employer FEIN");
          }
          const employeeFullName = `${claim.first_name} ${claim.last_name}`;
          portal.login(getLeaveAdminCredentials(claim.employer_fein));
          portal.checkNoticeForLeaveAdmin(
            submission.fineos_absence_id,
            employeeFullName,
            "approval"
          );
        });
      });
    }
  );

  it(
    "Should generate a notification for the Leave Administrator",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass([submit]);
      cy.unstash<Submission>("submission").then((submission) => {
        cy.unstash<ApplicationRequestBody>("claim").then((claim) => {
          const employeeFullName = `${claim.first_name} ${claim.last_name}`;
          const subjectEmployer = email.getNotificationSubject(
            `${claim.first_name} ${claim.last_name}`,
            "approval (employer)",
            submission.fineos_absence_id
          );
          // Check email for Employer/Leave Admin
          getEmails(
            {
              address: "gqzap.notifications@inbox.testmail.app",
              subject: subjectEmployer,
              messageWildcard: submission.fineos_absence_id,
              timestamp_from: submission.timestamp_from,
              debugInfo: { "Fineos Claim ID": submission.fineos_absence_id },
            },
            // Reduced timeout, since we have multiple tests that run prior to this.
            60000
          ).then(async (emails) => {
            const data = email.getNotificationData(emails[0].html);
            const dob =
              claim.date_of_birth?.replace(/-/g, "/").slice(5) + "/****";
            expect(data.name).to.equal(employeeFullName);
            expect(data.dob).to.equal(dob);
            expect(data.applicationId).to.equal(submission.fineos_absence_id);
            expect(emails[0].html).to.contain(
              `/employers/applications/status/?absence_id=${submission.fineos_absence_id}`
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
      cy.dependsOnPreviousPass([submit]);
      cy.unstash<Submission>("submission").then((submission) => {
        cy.unstash<ApplicationRequestBody>("claim").then((claim) => {
          const subjectClaimant = email.getNotificationSubject(
            `${claim.first_name} ${claim.last_name}`,
            "approval (claimant)",
            submission.fineos_absence_id
          );
          // Check email for Claimant/Employee
          getEmails(
            {
              address: "gqzap.notifications@inbox.testmail.app",
              subject: subjectClaimant,
              messageWildcard: submission.fineos_absence_id,
              timestamp_from: submission.timestamp_from,
              debugInfo: { "Fineos Claim ID": submission.fineos_absence_id },
            },
            // Reduced timeout, since we have multiple tests that run prior to this.
            30000
          ).should("not.be.empty");
        });
      });
    }
  );
});
