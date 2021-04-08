import * as portal from "../../../tests/common/actions/portal";
import { beforePortal } from "../../../tests/common/before";

describe("Submit a REDUCED LEAVE bonding claim and adjucation approval - BHAP8", () => {
  it("As a claimant, I should be able to submit a Reduced Leave claim (BHAP8) through the portal", () => {
    beforePortal();

    cy.task("generateClaim", "BHAP8").then((claim) => {
      const application: ApplicationRequestBody = claim.claim;
      const paymentPreference = claim.paymentPreference;

      const credentials: Credentials = {
        username: Cypress.env("E2E_PORTAL_USERNAME"),
        password: Cypress.env("E2E_PORTAL_PASSWORD"),
      };
      portal.login(credentials);
      portal.goToDashboardFromApplicationsPage();

      // Continue Creating Claim
      portal.startClaim();
      portal.onPage("start");
      portal.agreeToStart();
      portal.hasClaimId();
      portal.onPage("checklist");

      // Submit Claim
      portal.submitClaimPartOne(application);
      portal.waitForClaimSubmission().then((data) => {
        cy.stash("submission", {
          application_id: data.application_id,
          fineos_absence_id: data.fineos_absence_id,
          timestamp_from: Date.now(),
        });
      });
      portal.submitClaimPartsTwoThree(application, paymentPreference);
    });
  });
});
