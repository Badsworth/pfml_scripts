import * as portal from "../../../tests/common/actions/portal";
import { fineos } from "../../../tests/common/actions";
import { beforeFineos } from "../../../tests/common/before";
import { beforePortal } from "../../../tests/common/before";
import { getFineosBaseUrl } from "../../../config";

describe("Request for More Information (notificatins/notices)", () => {
  it(
    "Create a financially ineligible claim that is denied by an agent",
    { baseUrl: getFineosBaseUrl() },
    () => {
      beforeFineos();
      cy.visit("/");

      // Generate Creds for Registration/Login - submit claim via API
      cy.task("generateCredentials", false).then((credentials) => {
        cy.stash("credentials", credentials);
        cy.task("registerClaimant", credentials).then(() => {
          cy.task("generateClaim", {
            claimType: "BHAP1",
            employeeType: "financially eligible",
          }).then((claim: SimulationClaim) => {
            cy.stash("claim", claim);
            cy.stash("timestamp_from", Date.now());
            cy.task("submitClaimToAPI", {
              ...claim,
              credentials,
            } as SimulationClaim).then((response) => {
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
            applicationId: applicationId,
            document_type: "Request for more Information",
          },
          { timeout: 300000 }
        );
        cy.log("Finished waiting for documents");
      });
      cy.unstash<string>("fineos_absence_id").then((caseNumber) => {
        cy.visit("/applications");
        cy.contains("article", caseNumber).within(() => {
          cy.contains("a", "Request for more information").should("be.visible");
        });
      });
    });
  });

  // ATT: Being commented out until Email Delivery is confirmed
  // Check for email notification in regards to providing additional information
  // it("As a claimant, I should receive a notification requesting additional info", () => {
  //   cy.unstash<SimulationClaim>("claim").then((claim) => {
  //     if (
  //       !claim.claim.employer_fein ||
  //       !claim.claim.first_name ||
  //       !claim.claim.last_name
  //     ) {
  //       throw new Error("This employer has no FEIN");
  //     }
  //     cy.unstash<string>("fineos_absence_id").then((caseNumber) => {
  //       cy.unstash<number>("timestamp_from").then((timestamp_from) => {
  //         cy.task("getEmails", {
  //           address: "gqzap.notifications@inbox.testmail.app",
  //           // subject: `Action required: Respond to ${claim.claim.first_name} ${claim.claim.last_name}'s paid leave application`,
  //           subject: `Action required: Provide additional information for your paid leave application ${caseNumber}`,
  //           timestamp_from,
  //         }).then((emails) => {
  //           expect(emails.length).to.be.greaterThan(0);
  //           expect(emails[0].html).to.contain(
  //             `/employers/applications/new-application/?absence_id=${caseNumber}`
  //           );
  //         });
  //       });
  //     });
  //   });
  // });
});
