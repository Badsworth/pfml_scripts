import { fineos, portal, email } from "../../../tests/common/actions";
import {
  bailIfThisTestFails,
  beforeFineos,
  beforePortal,
} from "../../../tests/common/before";
import { getFineosBaseUrl, getLeaveAdminCredentials } from "../../../config";
import { ApplicationResponse } from "../../../../src/api";
import { Submission } from "../../../../src/types";

describe("Denial Notification and Notice", () => {
  it("Submit a financially ineligible claim to API", () => {
    beforePortal();
    bailIfThisTestFails();

    cy.visit("/");
    cy.task("generateCredentials", false).then((credentials) => {
      cy.task("registerClaimant", credentials).then(() => {
        cy.task("generateClaim", {
          claimType: "BHAP1",
          employeeType: "financially ineligible",
        }).then((claim: SimulationClaim) => {
          cy.task("submitClaimToAPI", {
            ...claim,
            credentials,
          } as SimulationClaim).then((responseData: ApplicationResponse) => {
            if (!responseData.fineos_absence_id) {
              throw new Error("FINEOS ID must be specified");
            }
            cy.stash("claim", claim.claim);
            cy.stash("submission", {
              application_id: responseData.application_id,
              fineos_absence_id: responseData.fineos_absence_id,
              timestamp_from: Date.now(),
            });
            cy.stash("credentials", credentials);
          });
        });
      });
    });
  });

  it("Deny a claim", { baseUrl: getFineosBaseUrl() }, () => {
    beforeFineos();
    bailIfThisTestFails();
    cy.visit("/");
    cy.unstash<Submission>("submission").then((submission) => {
      fineos.visitClaim(submission.fineos_absence_id);
      fineos.assertClaimFinancialEligibility(false);
    });
    fineos.denyClaim("Claimant wages failed 30x rule");
    cy.wait(200);
    if (Cypress.env("E2E_ENVIRONMENT") === "performance") {
      fineos.closeReleaseNoticeTask("Denial Notice");
    }
  });

  // Check Legal Notice for both claimant/Leave-admin
  it("Checking Legal Notice for both claimant and Leave-Admin", () => {
    beforePortal();
    cy.unstash<Credentials>("credentials").then((credentials) => {
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

        // const portalBaseUrl = Cypress.env("E2E_PORTAL_BASEURL");
        // if (!portalBaseUrl) {
        //   throw new Error("Portal base URL must be set");
        // }
        // Cypress.config("baseUrl", portalBaseUrl);
        cy.visit("/applications");
        cy.contains("article", submission.fineos_absence_id).within(() => {
          cy.contains("a", "Denial notice").should("be.visible");
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
            "denial"
          );
        });
      });
    });
  });

  it("I should receive an 'application started' notification", () => {
    cy.unstash<ApplicationRequestBody>("claim").then((claim) => {
      cy.unstash<Submission>("submission").then((submission) => {
        const employeeFullName = `${claim.first_name} ${claim.last_name}`;
        const subject = email.getNotificationSubject(
          employeeFullName,
          "application started",
          submission.fineos_absence_id
        );
        cy.task<Email[]>(
          "getEmails",
          {
            address: "gqzap.notifications@inbox.testmail.app",
            subject: subject,
            timestamp_from: submission.timestamp_from,
          },
          { timeout: 180000 }
        ).then(async (emails) => {
          const emailContent = await email.getNotificationData(emails[0].html);
          if (typeof claim.date_of_birth !== "string") {
            throw new Error("DOB must be a string");
          }
          const dob = claim.date_of_birth.replace(/-/g, "/").slice(5) + "/****";
          expect(emailContent.name).to.equal(employeeFullName);
          expect(emailContent.dob).to.equal(dob);
          expect(emailContent.applicationId).to.equal(
            submission.fineos_absence_id
          );
        });
      });
    });
  });

  it("I should receive an 'denial (employer)' and 'denial (claimant)' notification", () => {
    cy.unstash<ApplicationRequestBody>("claim").then((claim) => {
      cy.unstash<Submission>("submission").then((submission) => {
        const employeeFullName = `${claim.first_name} ${claim.last_name}`;
        const subjectEmployer = email.getNotificationSubject(
          employeeFullName,
          "denial (employer)",
          submission.application_id
        );

        const subjectClaimant = email.getNotificationSubject(
          employeeFullName,
          "denial (claimant)",
          submission.application_id
        );

        cy.log(subjectEmployer);
        cy.task<Email[]>(
          "getEmails",
          {
            address: "gqzap.notifications@inbox.testmail.app",
            subject: subjectEmployer,
            timestamp_from: submission.timestamp_from,
          },
          { timeout: 180000 }
        ).then(async (emails) => {
          const emailContent = await email.getNotificationData(
            emails[0].html,
            "denial (employer)"
          );
          if (typeof claim.date_of_birth !== "string") {
            throw new Error("DOB must be a string");
          }
          const dob = claim.date_of_birth.replace(/-/g, "/").slice(5) + "/****";
          expect(emailContent.name).to.equal(employeeFullName);
          expect(emailContent.dob).to.equal(dob);
          expect(emailContent.applicationId).to.equal(
            submission.fineos_absence_id
          );
          expect(emails[0].html).to.include(
            `/employers/applications/status/?absence_id=${submission.fineos_absence_id}`
          );
        });

        // Check email for Claimant
        cy.task<Email[]>(
          "getEmails",
          {
            address: "gqzap.notifications@inbox.testmail.app",
            subject: subjectClaimant,
            timestamp_from: submission.timestamp_from,
          },
          { timeout: 180000 }
        ).then(async (emails) => {
          for (const emailSingle of emails) {
            email.getNotificationData(emailSingle.html).then((data) => {
              if (data.applicationId.includes(submission.fineos_absence_id)) {
                expect(data.applicationId).to.contain(
                  submission.fineos_absence_id
                );
              } else {
                throw new Error("No emails match the Fineos Absence ID");
              }
            });
          }
        });
      });
    });
  });
});
