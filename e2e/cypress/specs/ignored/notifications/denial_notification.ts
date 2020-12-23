import { getFineosBaseUrl } from "../../../config";
import { fineos, portal, email } from "../../../tests/common/actions";
import { beforeFineos, beforePortal } from "../../../tests/common/before";
import { ApplicationResponse } from "../../../../src/api";
import { Submission } from "../../../../src/types";

describe(
  "Denial Notification and Notice",
  {
    baseUrl: getFineosBaseUrl(),
  },
  () => {
    it("Submit a financially ineligible claim to API", () => {
      beforeFineos();
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
                throw new Error("FINOES ID must be specified");
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
      cy.visit("/");
      cy.unstash<Submission>("submission").then((submission) => {
        fineos.visitClaim(submission.fineos_absence_id);
      });
      fineos.denyClaim("Claimant wages failed 30x rule");
      cy.wait(200);
    });

    it(
      "As a claimant, I should see a denial notice reflected in the portal",
      {
        baseUrl: Cypress.env("PORTAL_BASEURL"),
      },
      () => {
        beforePortal();
        cy.unstash<Credentials>("credentials").then((credentials) => {
          portal.login(credentials);
          cy.unstash<Submission>("submission").then((submission) => {
            cy.log("Waiting for documents");
            cy.task(
              "waitForClaimDocuments",
              {
                credentials: credentials,
                applicationId: submission.application_id,
                document_type: "Denial Notice",
              },
              { timeout: 300000 }
            );
            cy.log("Finished waiting for documents");
            cy.contains("a", "View your applications").click();
            cy.contains("article", submission.fineos_absence_id).within(() => {
              cy.contains("a", "Denial notice").should("be.visible");
            });
          });
        });
      }
    );

    it("I should receive an 'application started' notification", () => {
      cy.unstash<ApplicationRequestBody>("claim").then((claim) => {
        cy.unstash<Submission>("submission").then((submission) => {
          const employeeFullName = `${claim.first_name} ${claim.last_name}`;
          const subject = email.getNotificationSubject(
            employeeFullName,
            "application started",
            submission.application_id
          );
          cy.task<Email[]>(
            "getEmails",
            {
              address: "gqzap.notifications@inbox.testmail.app",
              subject: subject,
              timestamp_from: submission.timestamp_from,
            },
            { timeout: 180000 }
          ).then((emails) => {
            const emailContent = email.getNotificationData(emails[0].html);
            if (typeof claim.date_of_birth !== "string") {
              throw new Error("DOB must be a string");
            }
            const dob =
              claim.date_of_birth.replace(/-/g, "/").slice(5) + "/****";
            expect(emailContent.name).to.equal(employeeFullName);
            expect(emailContent.dob).to.equal(dob);
            expect(emailContent.applicationId).to.equal(
              submission.fineos_absence_id
            );
          });
        });
      });
    });

    it("I should receive an 'denial (employer)' notification", () => {
      cy.unstash<ApplicationRequestBody>("claim").then((claim) => {
        cy.unstash<Submission>("submission").then((submission) => {
          const employeeFullName = `${claim.first_name} ${claim.last_name}`;
          const subject = email.getNotificationSubject(
            employeeFullName,
            "denial (employer)",
            submission.application_id
          );
          cy.log(subject);
          cy.task<Email[]>(
            "getEmails",
            {
              address: "gqzap.notifications@inbox.testmail.app",
              subject: subject,
              timestamp_from: submission.timestamp_from,
            },
            { timeout: 180000 }
          ).then((emails) => {
            const emailContent = email.getNotificationData(emails[0].html);
            if (typeof claim.date_of_birth !== "string") {
              throw new Error("DOB must be a string");
            }
            const dob =
              claim.date_of_birth.replace(/-/g, "/").slice(5) + "/****";
            expect(emailContent.name).to.equal(employeeFullName);
            expect(emailContent.dob).to.equal(dob);
            expect(emailContent.applicationId).to.equal(
              submission.fineos_absence_id
            );
          });
        });
      });
    });
  }
);
