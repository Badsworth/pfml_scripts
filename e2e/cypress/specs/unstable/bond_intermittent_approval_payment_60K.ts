import { portal, fineos } from "../../actions";
import { getFineosBaseUrl, getLeaveAdminCredentials } from "../../config";
import { Submission } from "../../../src/types";
import { config } from "../../actions/common";
import { assertValidClaim } from "../../../src/util/typeUtils";

describe("Submit bonding application via the web portal: Adjudication Approval, recording actual hours & payment checking", () => {
  const submissionTest = it("As a claimant, I should be able to submit a intermittent bonding application through the portal", () => {
    portal.before();
    cy.task("generateClaim", "BIAP60").then((claim) => {
      cy.stash("claim", claim);
      const application: ApplicationRequestBody = claim.claim;
      const paymentPreference = claim.paymentPreference;

      const credentials: Credentials = {
        username: config("PORTAL_USERNAME"),
        password: config("PORTAL_PASSWORD"),
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
        assertValidClaim(claim.claim);
        portal.login(getLeaveAdminCredentials(claim.claim.employer_fein));
        portal.selectClaimFromEmployerDashboard(
          submission.fineos_absence_id,
          "--"
        );
        portal.visitActionRequiredERFormPage(submission.fineos_absence_id);
        portal.respondToLeaveAdminRequest(false, true, true);
      });
    });
  });

  it(
    "CSR rep will approve intermittent bonding application",
    { retries: 0, baseUrl: getFineosBaseUrl() },
    () => {
      cy.dependsOnPreviousPass();
      fineos.before();
      cy.visit("/");
      cy.unstash<Submission>("submission").then((submission) => {
        fineos.intermittentClaimAdjudicationFlow(
          submission.fineos_absence_id,
          "Child Bonding",
          true
        );
      });
    }
  );

  it(
    "CSR rep will record actual hours reported by employee",
    { retries: 0, baseUrl: getFineosBaseUrl() },
    () => {
      cy.dependsOnPreviousPass();
      fineos.before();
      cy.visit("/");
      cy.unstash<DehydratedClaim>("claim").then((claim) => {
        cy.unstash<Submission>("submission").then((submission) => {
          fineos.visitClaim(submission.fineos_absence_id);
          fineos.assertClaimStatus("Approved");
          fineos.submitIntermittentActualHours(
            claim.metadata?.spanHoursStart as string,
            claim.metadata?.spanHoursEnd as string
          );
        });
      });
    }
  );

  it(
    "Should be able to confirm the weekly payment amount for a intermittent schedule",
    { baseUrl: getFineosBaseUrl() },
    () => {
      cy.dependsOnPreviousPass();
      fineos.before();
      cy.visit("/");

      cy.unstash<DehydratedClaim>("claim").then((claim) => {
        cy.unstash<Submission>("submission").then((submission) => {
          fineos.checkPaymentPreference(claim);
          fineos.visitClaim(submission.fineos_absence_id);
          fineos.assertClaimStatus("Approved");
          fineos.getIntermittentPaymentAmount().then((amount) => {
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
