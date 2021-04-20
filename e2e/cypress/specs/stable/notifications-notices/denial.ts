import { fineos, portal, email } from "../../../actions";
import { getFineosBaseUrl, getLeaveAdminCredentials } from "../../../config";
import { ApplicationResponse } from "../../../../src/api";
import { Submission } from "../../../../src/types";

describe("Denial Notification and Notice", () => {
  const credentials: Credentials = {
    username: Cypress.env("E2E_PORTAL_USERNAME"),
    password: Cypress.env("E2E_PORTAL_PASSWORD"),
  };

  const submit = it(
    "Given a fully denied claim",
    { baseUrl: getFineosBaseUrl() },
    () => {
      fineos.before();
      cy.visit("/");

      cy.task("generateClaim", "BHAP1INEL").then((claim) => {
        cy.task("submitClaimToAPI", {
          ...claim,
          credentials,
        }).then((responseData: ApplicationResponse) => {
          if (!responseData.fineos_absence_id) {
            throw new Error("FINEOS ID must be specified");
          }
          cy.stash("claim", claim.claim);
          cy.stash("submission", {
            application_id: responseData.application_id,
            fineos_absence_id: responseData.fineos_absence_id,
            timestamp_from: Date.now(),
          });
          fineos.visitClaim(responseData.fineos_absence_id);
          fineos.assertClaimFinancialEligibility(false);
          fineos.denyClaim("Claimant wages failed 30x rule");
          fineos.triggerNoticeRelease("Denial Notice");
        });
      });
    }
  );

  it(
    "Should generate a legal notice that the claimant can view",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass([submit]);
      portal.before();
      cy.unstash<Submission>("submission").then((submission) => {
        portal.login(credentials);
        cy.log("Waiting for documents");
        cy.task(
          "waitForClaimDocuments",
          {
            credentials: credentials,
            application_id: submission.application_id,
            document_type: "Denial Notice",
          },
          { timeout: 300000 }
        );
        cy.log("Finished waiting for documents");
        cy.visit("/applications");
        cy.contains("article", submission.fineos_absence_id).within(() => {
          cy.contains("a", "Denial notice").should("be.visible");
        });
      });
    }
  );

  it(
    "Should generate a legal notice that the Leave Administrator can view",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass([submit]);
      portal.before();
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
            "denial"
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
              60000
            )
            .then(async (emails) => {
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

  it("Should generate a notification for the claimant", { retries: 0 }, () => {
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
          .should("not.be.empty");
      });
    });
  });
});
