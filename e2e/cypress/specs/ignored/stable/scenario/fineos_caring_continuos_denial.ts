import { extractLeavePeriod } from "../../../../../src/util/claims";
import { LeaveReason } from "types";
import { portal, fineos } from "../../../../actions";
import { getFineosBaseUrl, getLeaveAdminCredentials } from "../../../../config";
import { assertValidClaim } from "../../../../../src/util/typeUtils";

describe("Create a new continuous leave, caring leave claim in FINEOS", () => {
  const fineosSubmission = it(
    "Should be able to create a claim",
    { baseUrl: getFineosBaseUrl() },
    () => {
      fineos.before();
      cy.visit("/");
      cy.task("generateClaim", "CDENY2").then((claim) => {
        cy.stash("claim", claim);
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
        fineos.createNotification(startDate, endDate, "caring", claim.claim);
        cy.get("a[name*='CaseMapWidget']")
          .invoke("text")
          .then((text) => {
            const fineos_absence_id = text.slice(24);
            cy.stash("fineos_absence_id", fineos_absence_id);
            cy.log(fineos_absence_id);
            const reason = claim.claim.leave_details?.reason;
            fineos.visitClaim(fineos_absence_id);
            fineos.assertClaimStatus("Adjudication");
            fineos.reviewMailedDocumentsWithTasks(
              fineos_absence_id,
              reason as LeaveReason,
              "Caring Certification Review",
              true
            );
          });
      });
    }
  );

  const employerDenial = it("Leave admin will submit ER denial for employee", () => {
    cy.dependsOnPreviousPass([fineosSubmission]);
    portal.before();
    cy.unstash<DehydratedClaim>("claim").then((claim) => {
      cy.unstash<string>("fineos_absence_id").then((fineos_absence_id) => {
        assertValidClaim(claim.claim);
        portal.login(getLeaveAdminCredentials(claim.claim.employer_fein));
        portal.selectClaimFromEmployerDashboard(fineos_absence_id, "--");
        portal.visitActionRequiredERFormPage(fineos_absence_id);
        portal.respondToLeaveAdminRequest(false, true, false, true);
      });
    });
  });

  it("CSR rep will deny claim", { baseUrl: getFineosBaseUrl() }, () => {
    cy.dependsOnPreviousPass([fineosSubmission, employerDenial]);
    fineos.before();
    cy.visit("/");
    cy.unstash<string>("fineos_absence_id").then((fineos_absence_id) => {
      fineos.visitClaim(fineos_absence_id);
      fineos.denyClaim("Covered family relationship not established");
    });
  });
});
