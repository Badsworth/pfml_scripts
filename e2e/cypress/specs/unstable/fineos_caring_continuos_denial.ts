import { fineos } from "../../actions";
import { extractLeavePeriod } from "../../../src/util/claims";
import { getFineosBaseUrl } from "../../config";
import { LeaveReason } from "types";

describe("Create a new continuous leave, military caregiver claim in FINEOS", () => {
  it(
    "Should be able to create a claim",
    { baseUrl: getFineosBaseUrl() },
    () => {
      fineos.before();
      cy.visit("/");
      cy.task("generateClaim", "CHAP2").then((claim) => {
        if (
          !claim.claim.first_name ||
          !claim.claim.last_name ||
          !claim.claim.tax_identifier
        ) {
          throw new Error("Claim is missing a first name, last name, or SSN.");
        }

        fineos.searchClaimantSSN(claim.claim.tax_identifier);
        fineos.clickBottomWidgetButton("OK");
        fineos.assertOnClaimantPage(
          claim.claim.first_name,
          claim.claim.last_name
        );
        const [startDate, endDate] = extractLeavePeriod(
          claim.claim,
          "continuous_leave_periods"
        );
        fineos.createNotification(startDate, endDate, "caring", claim.claim);
        cy.get("a[name*='CaseMapWidget']")
          .invoke("text")
          .then((text) => {
            const fineos_absence_id = text.slice(24);
            cy.log(fineos_absence_id);
            const reason = claim.claim.leave_details?.reason;
            fineos.visitClaim(fineos_absence_id);
            fineos.assertClaimStatus("Adjudication");
            fineos.mailedDocumentMarkEvidenceRecieved(
              fineos_absence_id,
              reason as LeaveReason,
              false
            );
            fineos.denyClaim("Claimant wages failed 30x rule");
            fineos.triggerNoticeRelease("Denial Notice");
          });
      });
    }
  );
});
