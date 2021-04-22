import { fineos } from "../../../actions";
import { getFineosBaseUrl } from "../../../config";
import { ApplicationResponse } from "../../../../src/api";

describe("Payment amounts", () => {
  it(
    "Verify the payment amount for a continuous bonding claim with a regular schedule",
    { baseUrl: getFineosBaseUrl() },
    () => {
      fineos.before();
      cy.visit("/");
      // Generate Creds for Registration/Login - submit claim via API
      cy.task("generateClaim", "Jill").then((claim) => {
        if (!claim.claim.employer_fein) {
          throw new Error("Claim has no Employer FEIN");
        }
        cy.task("submitClaimToAPI", {
          ...claim,
        }).then((response: ApplicationResponse) => {
          if (typeof response.fineos_absence_id !== "string") {
            throw new Error("Response must include FINEOS absence ID");
          }
          fineos.checkPaymentPreference(claim);
          fineos.claimAdjudicationFlow(response.fineos_absence_id, true);
          fineos.getPaymentAmount().then((amount) => {
            expect(amount).to.eq("461.54");
          });
        });
      });
    }
  );
});
