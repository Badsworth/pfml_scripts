import * as portal from "../../../tests/common/actions/portal";
import { fineos } from "../../../tests/common/actions";
import { beforeFineos } from "../../../tests/common/before";
import { beforePortal } from "../../../tests/common/before";
import { getFineosBaseUrl } from "../../../config";

describe("Submit a bonding claim and adjucation approval - BHAP1", () => {
  it("As a claimant, I should be able to submit a claim (BHAP1) through the portal", () => {
    beforePortal();

    cy.task("generateClaim", {
      claimType: "BHAP1",
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
      portal.login(credentials);

      // Continue Creating Claim
      portal.startClaim();
      portal.onPage("start");
      portal.agreeToStart();
      portal.hasClaimId();
      portal.onPage("checklist");

      // Submit Claim
      portal.submitClaimNoLeaveCert(application, paymentPreference);
    });
  });

  // Prepare for adjudication approval
  it(
    "As a CSR (Savilinx), I should be able to Approve a BHAP1 claim submission",
    { baseUrl: getFineosBaseUrl() },
    () => {
      beforeFineos();
      cy.visit("/");

      cy.unstash<string>("claimNumber").then((claimNumber) => {
        fineos.claimAdjudicationMailedDoc(claimNumber);
      });
    }
  );
});
