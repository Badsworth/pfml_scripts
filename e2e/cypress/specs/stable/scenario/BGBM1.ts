import * as portal from "../../../tests/common/actions/portal";
import { fineos } from "../../../tests/common/actions";
import { beforeFineos } from "../../../tests/common/before";
import { beforePortal } from "../../../tests/common/before";
import { getFineosBaseUrl } from "../../../config";

describe("Submit a bonding claim and adjucation approval - BHAP1", () => {
  it("As a claimant, I should be able to submit a claim (BHAP1) through the portal", () => {
    beforePortal();

    cy.task("generateClaim", {
      claimType: "BGBM1",
      employeeType: "financially eligible",
    }).then((claim: SimulationClaim) => {
      if (!claim) {
        throw new Error("Claim Was Not Generated");
      }
      cy.log("generated claim", claim.claim);
      const application: ApplicationRequestBody = claim.claim;
      const paymentPreference = claim.paymentPreference;

      const credentials: Credentials = {
        username: Cypress.env("E2E_PORTAL_USERNAME"),
        password: Cypress.env("E2E_PORTAL_PASSWORD"),
      };
      cy.stash("credentials", credentials);
      portal.login(credentials);

      // Continue Creating Claim
      portal.startClaim();
      portal.onPage("start");
      portal.agreeToStart();
      portal.hasClaimId();
      portal.onPage("checklist");

      // Submit Claim
      portal.submitClaimPartOne(application);
      cy.wait("@submitClaimResponse").then((xhr) => {
        if (!xhr.response || !xhr.response.body) {
          throw new Error("No response body detected");
        }
        const body =
          typeof xhr.response.body === "string"
            ? JSON.parse(xhr.response.body)
            : xhr.response.body;
        cy.stashLog("claimNumber", body.data.fineos_absence_id);
        cy.stashLog("applicationId", body.data.application_id);
      });
      portal.submitPartThreeNoLeaveCert(application, paymentPreference);
    });
  });

  // Prepare for adjudication approval
  it(
    "As a CSR (Savilinx), I should be able to Approve a BGBM1 claim submission",
    { baseUrl: getFineosBaseUrl() },
    () => {
      beforeFineos();
      cy.visit("/");

      cy.unstash<string>("claimNumber").then((claimNumber) => {
        fineos.claimAdjudicationMailedDoc(claimNumber);
      });
    }
  );

  // Check Application card in portal for document uploaded in Fineos
  it("I should be able to see that a document has been uploaded in the portal", () => {
    beforePortal();
    cy.unstash<Credentials>("credentials").then((credentials) => {
      portal.login(credentials);
      cy.unstash<string>("applicationId").then((application_id) => {
        portal.goToIdUploadPage(application_id);
        cy.contains(
          "form",
          "Upload your Massachusetts driver’s license or ID card"
        )
          .find("h3")
          .should("have.length", 1);
      });
    });
  });
});
