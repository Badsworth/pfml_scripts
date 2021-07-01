import { fineos } from "../../actions";
import { extractLeavePeriod } from "../../../src/util/claims";
import { getFineosBaseUrl } from "../../config";
import { assertValidClaim } from "../../../src/util/typeUtils";
import {addHistoricalAbsenceCase} from "../../actions/fineos";

describe("Create a new continuous leave, medical leave claim in FINEOS and adding Historical Absence case", () => {
  it(
    "Should be able to create a claim",
    { baseUrl: getFineosBaseUrl() },
    () => {
      fineos.before();
      cy.visit("/");
      cy.task("generateClaim", "HIST_CASE").then((claim) => {
        assertValidClaim(claim.claim);

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
        fineos.createNotification(startDate, endDate, "medical", claim.claim);
        cy.get("a[name*='CaseMapWidget']")
          .invoke("text")
          .then((text) => {
            const fineos_absence_id = text.slice(24);
            cy.log(fineos_absence_id);
            fineos.visitClaim(fineos_absence_id);
            fineos.assertClaimStatus("Adjudication");
            fineos.addHistoricalAbsenceCase(fineos_absence_id);
          });
      });
    }
  );
});

