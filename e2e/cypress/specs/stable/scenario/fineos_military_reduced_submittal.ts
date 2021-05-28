import { fineos } from "../../../actions";
import { extractLeavePeriod } from "../../../../src/util/claims";
import { getFineosBaseUrl } from "../../../config";

describe("Create a new continuous leave, military caregiver claim in FINEOS", () => {
  it(
    "Should be able to create a claim",
    { baseUrl: getFineosBaseUrl() },
    () => {
      fineos.before();
      cy.visit("/");
      cy.task("generateClaim", "MIL_RED").then((claim) => {
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
          "reduced_schedule_leave_periods"
        );
        fineos.createNotification(startDate, endDate, "military", claim.claim);
        cy.get("a[name*='CaseMapWidget']")
          .invoke("text")
          .then((text) => {
            const fineos_absence_id = text.slice(24);
            cy.log(fineos_absence_id);
            fineos.visitClaim(fineos_absence_id);
            fineos.assertClaimStatus("Adjudication");
          });
      });
    }
  );
});
