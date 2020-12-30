import * as portal from "../../../tests/common/actions/portal";
import { beforePortal } from "../../../tests/common/before";

describe("Submit a REDUCED LEAVE bonding claim and adjucation approval - BHAP8", () => {
  it("As a claimant, I should be able to submit a Reduced Leave claim (BHAP8) through the portal", () => {
    beforePortal();

    cy.task("generateClaim", {
      claimType: "BHAP9",
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
      portal.submitClaimPortal(application, paymentPreference);
    });
  });
});
