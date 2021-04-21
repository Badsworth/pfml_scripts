import { fineos } from "../../actions";
import { getFineosBaseUrl } from "../../config";
import { ApplicationResponse } from "../../../src/api";

describe("Payment amounts", () => {
  it(
    "Verify the payment amount for an intermittent bonding claim with 20 hrs work week schedule",
    { baseUrl: getFineosBaseUrl() },
    () => {
      fineos.before();
      cy.visit("/");
      // Generate Creds for Registration/Login - submit claim via API
      cy.task("generateClaim", "Sally").then((claim) => {
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
          fineos.intermittentClaimAdjudicationFlow(
            response.fineos_absence_id,
            true
          );
          fineos.submitIntermittentActualHours(4, 4);
          fineos.getIntermittentPaymentAmount().then((amount) => {
            expect(amount).to.eq("800.09");
          });
        });
      });
    }
  );
});
