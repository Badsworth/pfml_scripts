import { fineos, portal } from "../../tests/common/actions";
import { beforeFineos } from "../../tests/common/before";
import { beforePortal } from "../../tests/common/before";
import { getFineosBaseUrl } from "../../config";
import { Submission } from "../../../src/types";

describe("Submit a bonding claim with other income and other leave - BHAP1", () => {
  const submit = it("As a claimant, I submit a BHAP1 claim with other leave and other income through the portal", () => {
    beforePortal();

    cy.task("generateClaim", "BHAP1").then((claim) => {
      if (!claim) {
        throw new Error("Claim Was Not Generated");
      }
      cy.stash("claim", claim);
      const application = claim.claim;
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
      portal.submitClaimPartOne(application, true);
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
  // Check for Other Leave Document
  it(
    "In Fineos, check for Other Leave E-Form",
    { baseUrl: getFineosBaseUrl() },
    () => {
      cy.dependsOnPreviousPass([submit]);
      beforeFineos();
      cy.unstash<Submission>("submission").then((submission) => {
        cy.visit("/");
        fineos.findOtherLeaveEForm(submission.fineos_absence_id);
      });
    }
  );
});
