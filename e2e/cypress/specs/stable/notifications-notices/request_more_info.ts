import { fineos, portal, email } from "../../../tests/common/actions";
import {
  bailIfThisTestFails,
  beforeFineos,
} from "../../../tests/common/before";
import { beforePortal } from "../../../tests/common/before";
import { getFineosBaseUrl } from "../../../config";

describe(
  "Request for More Information (notifications/notices)",
  { retries: 0 },
  () => {
    it(
      "Create a financially eligible claim that is denied by an agent",
      { baseUrl: getFineosBaseUrl() },
      () => {
        beforeFineos();
        bailIfThisTestFails();

        cy.visit("/");

        // Generate Creds for Registration/Login - submit claim via API
        cy.task("generateCredentials").then((credentials) => {
          cy.stash("credentials", credentials);
          cy.task("registerClaimant", credentials).then(() => {
            cy.task("generateClaim", "BHAP1").then((claim) => {
              cy.stash("claim", claim.claim);
              cy.stash("timestamp_from", Date.now());
              cy.task("submitClaimToAPI", {
                ...claim,
                credentials,
              }).then((response) => {
                console.log(response);
                cy.wrap(response.fineos_absence_id).as("fineos_absence_id");
                cy.stashLog("fineos_absence_id", response.fineos_absence_id);
                cy.stashLog("applicationId", response.application_id);
              });
            });
          });
        });

        // Request for additional Info in Fineos
        cy.get<string>("@fineos_absence_id").then((fineos_absence_id) => {
          fineos.visitClaim(fineos_absence_id);
          fineos.additionalEvidenceRequest(fineos_absence_id);
          switch (Cypress.env("E2E_ENVIRONMENT")) {
            case "training":
            case "uat":
              fineos.closeReleaseNoticeTask("Request for more Information");
              break;

            case "performance":
            case "test":
            case "stage":
              fineos.triggerNoticeRelease("Request for more Information");
              break;

            default:
              throw new Error("Env Not Recognized - Try Again!");
          }
        });
      }
    );

    // Check for Legal Notice in claimant Portal
    it("As a claimant, I should see a request for additional info notice reflected in the portal", () => {
      beforePortal();

      cy.unstash<Credentials>("credentials").then((credentials) => {
        portal.login(credentials);
        cy.unstash<string>("applicationId").then((applicationId) => {
          cy.log("Waiting for documents");
          cy.task(
            "waitForClaimDocuments",
            {
              credentials: credentials,
              application_id: applicationId,
              document_type: "Request for more Information",
            },
            { timeout: 300000 }
          );
          cy.log("Finished waiting for documents");
        });
        cy.unstash<string>("fineos_absence_id").then((caseNumber) => {
          cy.visit("/applications");
          cy.contains("article", caseNumber).within(() => {
            cy.contains("a", "Request for more information").should(
              "be.visible"
            );
          });
        });
      });
    });

    // Check for email notification in regards to providing additional information
    it("As a claimant, I should receive a notification requesting additional info", () => {
      cy.unstash<ApplicationRequestBody>("claim").then((claim) => {
        if (!claim.employer_fein || !claim.first_name || !claim.last_name) {
          throw new Error("This employer has no FEIN");
        }
        cy.unstash<string>("fineos_absence_id").then((caseNumber) => {
          cy.unstash<number>("timestamp_from").then((timestamp_from) => {
            const employeeFullName = `${claim.first_name} ${claim.last_name}`;
            const subjectClaimant = email.getNotificationSubject(
              employeeFullName,
              "request for additional info",
              caseNumber
            );
            cy.log(subjectClaimant);

            // Check email notification for claimant
            cy.task("getEmails", {
              address: "gqzap.notifications@inbox.testmail.app",
              subject: subjectClaimant,
              timestamp_from,
            }).then(async (emails) => {
              const emailContent = await email.getNotificationData(
                emails[0].html
              );
              expect(emails.length).to.be.greaterThan(0);
              expect(emailContent.applicationId).to.contain(caseNumber);
            });
          });
        });
      });
    });
  }
);
