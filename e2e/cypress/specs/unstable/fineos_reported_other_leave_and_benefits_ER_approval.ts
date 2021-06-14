import { extractLeavePeriod } from "../../../src/util/claims";
import { assertValidClaim } from "../../../src/util/typeUtils";
import { fineos, fineosPages } from "../../actions";
import { config } from "../../actions/common";
import { getFineosBaseUrl } from "../../config";

describe("Claimant can call call-center to submit a claim for leave with other leaves and benefits", () => {
  if (config("FINEOS_HAS_UPDATED_EFORMS") === "true") {
    it(
      "CPS Agent can enter a claim with Concurrent (employer sponsored) leave and employer sponsored benefits",
      { baseUrl: getFineosBaseUrl() },
      () => {
        fineos.before();
        cy.visit("/");
        cy.task("generateClaim", "MIL_RED_OLB").then((claim) => {
          assertValidClaim(claim.claim);
          cy.stash("claim", claim.claim);
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
          fineos.createNotification(
            startDate,
            endDate,
            "military",
            claim.claim
          );
          cy.get("a[name*='CaseMapWidget']")
            .invoke("text")
            .then((text) => {
              const fineos_absence_id = text.slice(24);

              cy.stash("submission", {
                timestamp_from: Date.now(),
                fineos_absence_id,
              });

              fineosPages.ClaimPage.visit(fineos_absence_id).documents(
                (documentsPage) => {
                  const {
                    employer_benefits,
                    previous_leaves_other_reason,
                    previous_leaves_same_reason,
                    other_incomes,
                    concurrent_leave,
                  } = claim.claim;
                  documentsPage
                    .submitOtherBenefits({
                      employer_benefits: employer_benefits?.filter(
                        (b) => b.benefit_type !== "Accrued paid leave"
                      ),
                      other_incomes,
                    })
                    .submitOtherLeaves({
                      previous_leaves_other_reason,
                      previous_leaves_same_reason,
                      concurrent_leave,
                    });
                }
              );
            });
        });
      }
    );
    /**
     * @todo Functionality needed for these tests will be available starting June 2nd.
     */
    it("LA can review and approve a claim");
    it("CPS agent can approve the claim and check for possible reductions");
  } else {
    it("Does not run", () => {
      cy.log(
        "This test did not execute because this environment does not have the updated Fineos eForms."
      );
    });
  }
});
