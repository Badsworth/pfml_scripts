import { getFineosBaseUrl } from "../../../config";
import { fineos, portal } from "../../../tests/common/actions";
import { beforeFineos, beforePortal } from "../../../tests/common/before";

describe("Denial Notice", () => {
  it(
    "Create a financially ineligible claim that is denied by an agent",
    { baseUrl: getFineosBaseUrl() },
    () => {
      beforeFineos();
      cy.visit("/");

      // // Generate and submit the claim with a brand new claimant.
      cy.task("generateCredentials", false).then((credentials) => {
        cy.stash("credentials", credentials);
        cy.task("registerClaimant", credentials).then(() => {
          cy.task("generateClaim", {
            claimType: "BHAP1",
            employeeType: "financially ineligible",
          }).then((claim: SimulationClaim) => {
            cy.task("submitClaimToAPI", {
              ...claim,
              credentials,
            } as SimulationClaim).then((response) => {
              cy.wrap(response.fineos_absence_id).as("fineos_absence_id");
              cy.stashLog("fineos_absence_id", response.fineos_absence_id);
              cy.stashLog("applicationId", response.application_id);
            });
          });
        });
      });
      // Deny the claim as an agent.
      cy.get<string>("@fineos_absence_id").then((caseNumber) => {
        fineos.visitClaim(caseNumber);
        fineos.denyClaim("Claimant wages failed 30x rule");
      });
    }
  );

  it("As a claimant, I should see a denial notice reflected in the portal", () => {
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
            document_type: "Denial Notice",
          },
          { timeout: 300000 }
        );
        cy.log("Finished waiting for documents");
      });
      cy.unstash<string>("fineos_absence_id").then((caseNumber) => {
        cy.visit("/applications");
        cy.contains("article", caseNumber).within(() => {
          cy.contains("a", "Denial notice").should("be.visible");
        });
      });
    });
  });
});
