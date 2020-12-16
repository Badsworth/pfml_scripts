import { beforePortal, beforeFineos } from "../../../../tests/common/before";
import { fineos, portal } from "../../../../tests/common/actions";
import { getFineosBaseUrl, getLeaveAdminCredentials } from "../../../../config";

describe("Employer Responses", () => {
  it("As an employer, I should be able to submit a response for a claim immediately after submission", () => {
    beforePortal();
    cy.task("generateClaim", {
      claimType: "BHAP1",
      employeeType: "financially eligible",
    }).then((claim) => {
      const { employer_fein } = claim.claim;
      if (!(typeof employer_fein === "string")) {
        throw new Error("No employer_fein property was added to this claim.");
      }
      cy.task("submitClaimToAPI", claim).then((response) => {
        cy.stash("fineos_absence_id", response.fineos_absence_id);
        portal.login(getLeaveAdminCredentials(employer_fein));
        portal.respondToLeaveAdminRequest(
          response.fineos_absence_id,
          false,
          false,
          true
        );
      });
    });
  });

  it(
    "In Fineos, I should see the employer's response recorded",
    { baseUrl: getFineosBaseUrl() },
    () => {
      beforeFineos();
      cy.unstash<string>("fineos_absence_id").then((claimNumber) => {
        fineos.loginSavilinx();
        fineos.visitClaim(claimNumber);
        fineos.assertClaimHasLeaveAdminApproval();
      });
    }
  );
});
