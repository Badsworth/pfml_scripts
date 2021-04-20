import { fineos, portal } from "../../../actions";
import { getFineosBaseUrl } from "../../../config";
import { Submission } from "../../../../src/types";

describe("Submit a bonding claim and adjudication approval - BHAP1", () => {
  const submissionTest = it("As a claimant, I should be able to submit a claim (BHAP1) through the portal", () => {
    portal.before();
    cy.task("generateClaim", "BHAP1").then((claim) => {
      cy.stash("claim", claim.claim);
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

  it(
    "CSR rep should prepare claim for Adjudication",
    { baseUrl: getFineosBaseUrl() },
    () => {
      cy.dependsOnPreviousPass([submissionTest]);
      fineos.before();
      cy.visit("/");

      cy.unstash<Submission>("submission").then((submission) => {
        fineos.claimAdjudicationFlow(submission.fineos_absence_id);
      });
    }
  );
});
