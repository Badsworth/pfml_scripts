import { fineos, portal } from "../../../actions";
import { getFineosBaseUrl, getLeaveAdminCredentials } from "../../../config";
import { Submission } from "../../../../src/types";
import { config } from "../../../actions/common";
import { assertValidClaim } from "../../../../src/util/typeUtils";

describe("Submit a bonding claim and adjucation approval - BHAP1", () => {
  const submissionTest =
    it("As a claimant, I should be able to submit a continous bonding application through the portal", () => {
      portal.before();
      cy.task("generateClaim", "MCAP_NODOC").then((claim) => {
        cy.stash("claim", claim);
        const application: ApplicationRequestBody = claim.claim;
        const paymentPreference = claim.paymentPreference;

        const credentials: Credentials = {
          username: config("PORTAL_USERNAME"),
          password: config("PORTAL_PASSWORD"),
        };
        cy.stash("credentials", credentials);
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
        portal.submitPartsTwoThreeNoLeaveCert(paymentPreference);
      });
    });

  const adjudicate = it(
    "Should check hours worked per week/upload state managed document/mark evidence received (Fineos)",
    { baseUrl: getFineosBaseUrl() },
    () => {
      cy.dependsOnPreviousPass([submissionTest]);
      fineos.before();
      cy.visit("/");

      cy.unstash<DehydratedClaim>("claim").then((claim) => {
        cy.unstash<Submission>("submission").then((submission) => {
          assertValidClaim(claim.claim);
          const reason = claim.claim.leave_details.reason;
          if (!reason) throw new Error(`No claim type given`);
          fineos.checkHoursWorkedPerWeek(
            submission.fineos_absence_id,
            claim.claim.hours_worked_per_week as number
          );
          fineos.mailedDocumentMarkEvidenceRecieved(
            submission.fineos_absence_id,
            reason
          );
        });
      });
    }
  );

  // Check Application card in portal for document uploaded in Fineos
  it("I should be able to see that a document has been uploaded in the portal", () => {
    cy.dependsOnPreviousPass([submissionTest, adjudicate]);
    portal.before();

    cy.unstash<Credentials>("credentials").then((credentials) => {
      portal.login(credentials);
      cy.unstash<Submission>("submission").then((submission) => {
        portal.goToUploadCertificationPage(submission.application_id);
        cy.contains("form", "Upload your certification form")
          .find("*[data-test='file-card']", { timeout: 30000 })
          .should("have.length", 1);
      });
    });
  });

  it("Should check for hours worked per week & report conflict on Employer Response Form", () => {
    cy.dependsOnPreviousPass();
    portal.before();
    cy.unstash<DehydratedClaim>("claim").then((claim) => {
      cy.unstash<Submission>("submission").then((submission) => {
        assertValidClaim(claim.claim);
        portal.login(getLeaveAdminCredentials(claim.claim.employer_fein));
        portal.visitActionRequiredERFormPage(submission.fineos_absence_id);
        portal.checkHoursPerWeekLeaveAdmin(
          claim.claim.hours_worked_per_week as number
        );
        portal.respondToLeaveAdminRequest(false, false, false);
      });
    });
  });
});
