import { fineos } from "../../tests/common/actions";
import { beforeFineos } from "../../tests/common/before";
import { getFineosBaseUrl, getLeaveAdminCredentials } from "../../config";
import { ApplicationResponse } from "../../../src/api";

describe("Payment amounts", () => {
  it(
    "Verify the payment amount for a continuous bonding claim with 20 hrs work week schedule",
    { baseUrl: getFineosBaseUrl() },
    () => {
      beforeFineos();
      cy.visit("/");
      // Generate Creds for Registration/Login - submit claim via API
      cy.task("generateCredentials").then((credentials) => {
        cy.task("registerClaimant", credentials).then(() => {
          cy.task("generateClaim", "Sally").then((claim) => {
            if (!claim.claim.employer_fein) {
              throw new Error("Claim has no Employer FEIN");
            }
            const employerCredentials = getLeaveAdminCredentials(
              claim.claim.employer_fein
            );
            cy.task("submitClaimToAPI", {
              ...claim,
              credentials,
              employerCredentials,
            }).then((response: ApplicationResponse) => {
              if (typeof response.fineos_absence_id !== "string") {
                throw new Error("Response must include FINEOS absence ID");
              }
              fineos.checkPaymentPreference(claim);
              // fineos.claimAdjudicationFlow(response.fineos_absence_id, true);
              fineos.claimInterAdjudicationFlow(response.fineos_absence_id, true);
              fineos.getPaymentAmount().then((amount) => {
                expect(amount).to.eq("800.09");
              });
            });
          });
        });
      });
    }
  );
});
