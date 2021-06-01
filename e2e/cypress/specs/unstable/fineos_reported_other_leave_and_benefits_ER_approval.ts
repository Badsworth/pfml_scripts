import { extractLeavePeriod } from "../../../src/util/claims";
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
        cy.task("generateClaim", "MIL_RED").then((claim) => {
          if (
            !claim.claim.first_name ||
            !claim.claim.last_name ||
            !claim.claim.tax_identifier
          ) {
            throw new Error(
              "Claim is missing a first name, last name, or SSN."
            );
          }
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
                  documentsPage
                    .submitOtherBenefits({
                      employer_benefits: [
                        {
                          benefit_amount_dollars: 1000,
                          benefit_amount_frequency: "In Total",
                          benefit_start_date: startDate.toISOString(),
                          benefit_type: "Short-term disability insurance",
                          is_full_salary_continuous: false,
                        },
                      ],
                    })
                    .submitOtherLeaves({
                      previousLeaves: [
                        {
                          type: "other_reason",
                          leave_reason: "Child bonding",
                          is_for_current_employer: true,
                          leave_minutes: 2400,
                          worked_per_week_minutes: 1200,
                          leave_start_date: "2021-01-15",
                          leave_end_date: "2021-01-01",
                        },
                      ],
                      accrued_leaves: [
                        {
                          benefit_type: "Accrued paid leave",
                          benefit_end_date: endDate.toISOString(),
                          benefit_start_date: startDate.toISOString(),
                        },
                      ],
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
