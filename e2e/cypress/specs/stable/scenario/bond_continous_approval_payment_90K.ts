import { fineos, portal } from "../../../actions";
import { getFineosBaseUrl, getLeaveAdminCredentials } from "../../../config";
import { Submission } from "../../../../src/types";

describe("Submit bonding application via the web portal: Adjudication Approval & payment checking", () => {
  const submissionTest = it("As a claimant, I should be able to submit a continous bonding application through the portal", () => {
    portal.before();
    cy.task("generateClaim", "BCAP90").then((claim) => {
      cy.stash("claim", claim);
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

  it("Leave admin will submit ER approval for employee", () => {
    cy.dependsOnPreviousPass([submissionTest]);
    portal.before();
    cy.unstash<DehydratedClaim>("claim").then((claim) => {
      cy.unstash<Submission>("submission").then((submission) => {
        portal.login(
          getLeaveAdminCredentials(claim.claim.employer_fein as string)
        );
        portal.respondToLeaveAdminRequest(
          submission.fineos_absence_id,
          false,
          true,
          true
        );
      });
    });
  });

  it(
    "CSR rep will approve continous bonding application",
    { baseUrl: getFineosBaseUrl() },
    () => {
      cy.dependsOnPreviousPass();
      fineos.before();
      cy.visit("/");
      cy.unstash<Submission>("submission").then((submission) => {
        fineos.claimAdjudicationFlow(submission.fineos_absence_id, true);
      });
    }
  );

  it(
    "Should be able to confirm the weekly payment amount",
    { baseUrl: getFineosBaseUrl() },
    () => {
      cy.dependsOnPreviousPass();
      fineos.before();
      cy.visit("/");

      cy.unstash<DehydratedClaim>("claim").then((claim) => {
        cy.unstash<Submission>("submission").then((submission) => {
          fineos.checkPaymentPreference(claim);
          fineos.visitClaim(submission.fineos_absence_id, "Approved");
          fineos.getPaymentAmount().then((amount) => {
            expect(
              amount,
              `Maximum weekly payment should be: $${claim.metadata?.expected_weekly_payment}`
            ).to.eq(claim.metadata?.expected_weekly_payment as string);
          });
        });
      });
    }
  );
});
