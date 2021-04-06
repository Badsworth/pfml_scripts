import { fineos, portal, email } from "../../tests/common/actions";
import { bailIfThisTestFails, beforeFineos } from "../../tests/common/before";
import { beforePortal } from "../../tests/common/before";
import { getFineosBaseUrl, getLeaveAdminCredentials } from "../../config";
import { ApplicationResponse } from "../../../src/api";
import { Submission } from "../../../src/types";

describe("Approval (notifications/notices)", { retries: 0 }, () => {
  it("Create a financially eligible claim in which an employer will respond", () => {
    beforePortal();
    bailIfThisTestFails();

    cy.visit("/");

    // Generate Creds for Registration/Login - submit claim via API
    cy.task("generateCredentials").then((credentials) => {
      cy.stash("credentials", credentials);
      cy.task("registerClaimant", credentials).then(() => {
        cy.task("generateClaim", "BHAP1").then((claim) => {
          cy.stash("claim", claim.claim);
          cy.task("submitClaimToAPI", {
            ...claim,
            credentials,
          }).then((response: ApplicationResponse) => {
            const timestamp_fromER = Date.now();
            cy.stash("submission", {
              application_id: response.application_id,
              fineos_absence_id: response.fineos_absence_id,
              timestamp_from: Date.now(),
            });

            if (typeof claim.claim.employer_fein !== "string") {
              throw new Error("Claim must include employer FEIN");
            }
            if (typeof response.fineos_absence_id !== "string") {
              throw new Error("Response must include FINEOS absence ID");
            }

            cy.log(
              "Checking email notification for Employer Response (Action Required)"
            );
            cy.task<Email[]>(
              "getEmails",
              {
                address: "gqzap.notifications@inbox.testmail.app",
                subject: `Action required: Respond to ${claim.claim.first_name} ${claim.claim.last_name}'s paid leave application`,
                messageWildcard: response.fineos_absence_id,
                timestamp_from: timestamp_fromER,
                fineos_absence_id: response.fineos_absence_id,
              },
              { timeout: 360000 }
            ).then((emails) => {
              expect(emails[0].html).to.contain(
                `/employers/applications/new-application/?absence_id=${response.fineos_absence_id}`
              );
            });

            // Access and fill out ER form
            portal.login(getLeaveAdminCredentials(claim.claim.employer_fein));
            portal.respondToLeaveAdminRequest(
              response.fineos_absence_id,
              false,
              true,
              true
            );
          });
        });
      });
    });
  });

  // Check for ER and approval claim in Fineos
  it(
    "In Fineos, complete an Adjudication Approval",
    { baseUrl: getFineosBaseUrl() },
    () => {
      beforeFineos();
      bailIfThisTestFails();

      cy.unstash<Submission>("submission").then((submission) => {
        cy.visit("/");
        fineos.claimAdjudicationFlow(submission.fineos_absence_id, true);
        switch (Cypress.env("E2E_ENVIRONMENT")) {
          case "training":
            fineos.closeReleaseNoticeTask("Approval Notice");
            break;

          case "performance":
          case "test":
          case "stage":
          case "uat":
            fineos.triggerNoticeRelease("Approval Notice");
            break;

          default:
            throw new Error("Env Not Recognized - Try Again!");
        }
      });
    }
  );

  // Check Legal Notice for both claimant/Leave-admin
  it("Checking Legal Notice and Notifications for both claimant and Leave-Admin", () => {
    beforePortal();
    cy.unstash<Credentials>("credentials").then((credentials) => {
      // Check Legal Notice for Claimaint
      portal.login(credentials);
      cy.unstash<Submission>("submission").then((submission) => {
        portal.login(credentials);
        cy.log("Waiting for documents");
        cy.task(
          "waitForClaimDocuments",
          {
            credentials: credentials,
            application_id: submission.application_id,
            document_type: "Approval Notice",
          },
          { timeout: 300000 }
        );
        cy.log("Finished waiting for documents");

        cy.visit("/applications");
        cy.contains("article", submission.fineos_absence_id).within(() => {
          cy.contains("a", "Approval notice").should("be.visible");
        });
        portal.logout();

        // Check Legal Notice for Leave-Admin
        cy.unstash<ApplicationRequestBody>("claim").then((claim) => {
          const employeeFullName = `${claim.first_name} ${claim.last_name}`;
          if (typeof claim.employer_fein !== "string") {
            throw new Error("Claim must include employer FEIN");
          }
          portal.login(getLeaveAdminCredentials(claim.employer_fein));
          portal.checkNoticeForLeaveAdmin(
            submission.fineos_absence_id,
            employeeFullName,
            "approval"
          );

          // Checking email notifications for both claimant and Leave-Admin
          if (!claim.employer_fein || !claim.first_name || !claim.last_name) {
            throw new Error("This employer has no FEIN");
          }
          const subjectEmployer = email.getNotificationSubject(
            employeeFullName,
            "approval (employer)",
            submission.fineos_absence_id
          );
          const subjectClaimant = email.getNotificationSubject(
            employeeFullName,
            "approval (claimant)",
            submission.fineos_absence_id
          );
          cy.log(subjectEmployer);
          cy.log(subjectClaimant);

          // Check email for Employer/Leave Admin
          cy.task<Email[]>(
            "getEmails",
            {
              address: "gqzap.notifications@inbox.testmail.app",
              subject: subjectEmployer,
              messageWildcard: submission.fineos_absence_id,
              timestamp_from: submission.timestamp_from,
              debugInfo: { "Fineos Claim ID": submission.fineos_absence_id },
            },
            { timeout: 180000 }
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

          // Check email for Claimant/Employee
          cy.task<Email[]>(
            "getEmails",
            {
              address: "gqzap.notifications@inbox.testmail.app",
              subject: subjectClaimant,
              messageWildcard: submission.fineos_absence_id,
              timestamp_from: submission.timestamp_from,
              debugInfo: { "Fineos Claim ID": submission.fineos_absence_id },
            },
            { timeout: 180000 }
          ).should("not.be.empty");
        });
      });
    });
  });
});
