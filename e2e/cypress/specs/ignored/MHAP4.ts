import { portal, fineos } from "../../actions";
import { getLeaveAdminCredentials, getFineosBaseUrl } from "../../config";
import { Submission } from "../../../src/types";
import { assertValidClaim } from "../../../src/util/typeUtils";

describe("Submitting a Medical pregnancy claim and adding bonding leave in Fineos", () => {
  it("Create a financially eligible claim (MHAP4) in which an employer will respond", () => {
    portal.before();

    cy.task("generateClaim", "MHAP4").then((claim) => {
      cy.task("submitClaimToAPI", claim).then((response) => {
        cy.stash("submission", {
          application_id: response.application_id,
          fineos_absence_id: response.fineos_absence_id,
          timestamp_from: Date.now(),
        });
        // Complete Employer Response
        assertValidClaim(claim.claim);

        portal.login(getLeaveAdminCredentials(claim.claim.employer_fein));
        portal.visitActionRequiredERFormPage(response.fineos_absence_id);
        portal.respondToLeaveAdminRequest(false, true, true);
      });
    });
    cy.wait(1000);
  });

  // Check for ER and approval claim in Fineos
  it(
    "In Fineos, complete an Adjudication Approval along w/adding Bonding Leave",
    { baseUrl: getFineosBaseUrl() },
    () => {
      fineos.before();
      cy.unstash<Submission>("submission").then((submission) => {
        cy.visit("/");
        fineos.claimAdjudicationFlow(
          submission.fineos_absence_id,
          "Serious Health Condition - Employee",
          true
        );
        fineos.addBondingLeaveFlow(new Date());
      });
    }
  );
});
