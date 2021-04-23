import { portal, fineos } from "../../../actions";

import { getFineosBaseUrl } from "../../../config";
import { Submission } from "../../../../src/types";

describe("Submit a medical claim and adjucation approval - MHAP1", () => {
  const submit = it("As a claimant, I should be able to submit a Medical Leave claim (MHAP1) through the portal", () => {
    portal.before();

    cy.task("generateClaim", "MHAP1").then((claim) => {
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
      portal.goToDashboardFromApplicationsPage();

      // Submit Claim
      portal.startClaim();
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

  // Prepare for adjudication approval
  it(
    "As a CSR (Savilinx), I should be able to Approve a MHAP1 claim submission",
    { baseUrl: getFineosBaseUrl() },
    () => {
      cy.dependsOnPreviousPass([submit]);
      fineos.before();
      cy.visit("/");

      cy.unstash<Submission>("submission").then((submission) => {
        fineos.claimAdjudicationFlow(submission.fineos_absence_id);
      });
    }
  );
});
