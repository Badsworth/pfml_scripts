import { extractLeavePeriod } from "../../../src/util/claims";
import { LeaveReason } from "types";
import { portal, fineos } from "../../actions";
import { getFineosBaseUrl, getLeaveAdminCredentials } from "../../config";
import { Submission } from "../../../src/types";

describe("Create a new continuous leave, caring leave claim in FINEOS", () => {
  const fineosSubmission = it(
    "Should be able to create a claim",
    { baseUrl: getFineosBaseUrl() },
    () => {
      fineos.before();
      cy.visit("/");
      cy.task("generateClaim", "CDENY2").then((claim) => {
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
            // fineos.mailedDocumentMarkEvidenceRecieved(
            //   fineos_absence_id,
            //   reason as LeaveReason,
            //   false,
            //   true
            // );
            fineos.reviewMailedDocumentsWithTasks(
              fineos_absence_id,
              reason as LeaveReason,
              false,
              true
            );
            // fineos.denyClaim("Evidence documents fail requirements");
            // fineos.triggerNoticeRelease("Denial Notice");
          });
      });
    }
  );

  it("Leave admin will submit ER approval for employee", () => {
    cy.dependsOnPreviousPass([fineosSubmission]);
    portal.before();
    cy.unstash<DehydratedClaim>("claim").then((claim) => {
      cy.unstash<Submission>("submission").then((submission) => {
        portal.login(
          getLeaveAdminCredentials(claim.claim.employer_fein as string)
        );
        portal.selectClaimFromEmployerDashboard(
          submission.fineos_absence_id,
          "--"
        );
        portal.vistActionRequiredERFormPage(submission.fineos_absence_id);
        portal.respondToLeaveAdminRequest(false, true, false, true);
      });
    });
  });
});
