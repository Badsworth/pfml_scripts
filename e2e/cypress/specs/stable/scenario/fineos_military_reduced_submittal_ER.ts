import { fineos, portal } from "../../../actions";
import { extractLeavePeriod } from "../../../../src/util/claims";
import { getFineosBaseUrl, getLeaveAdminCredentials } from "../../../config";
import { assertValidClaim } from "../../../../src/util/typeUtils";
import { ClaimPage } from "../../../actions/fineos.pages";
import { Submission } from "../../../../src/types";

describe("Create a new continuous leave, military caregiver claim in FINEOS", () => {
  const claimSubmission = it(
    "Should be able to create a claim",
    { baseUrl: getFineosBaseUrl() },
    () => {
      fineos.before();
      cy.visit("/");
      cy.task("generateClaim", "MIL_RED").then((claim) => {
        assertValidClaim(claim.claim);
        cy.stash("claim", claim);

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
            cy.stash("submission", { fineos_absence_id });

            ClaimPage.visit(fineos_absence_id).adjudicate((adjudication) => {
              adjudication.evidence((evidence) => {
                claim.documents.forEach((doc) =>
                  evidence.receive(doc.document_type)
                );
                evidence.receive("Covered Service Member Identification Proof");
              });
            });
          });
      });
    }
  );

  it("LA can review and deny the claim", () => {
    cy.dependsOnPreviousPass([claimSubmission]);
    portal.before();
    cy.unstash<DehydratedClaim>("claim").then(({ claim }) => {
      cy.unstash<Submission>("submission").then((submission) => {
        assertValidClaim(claim);
        portal.login(getLeaveAdminCredentials(claim.employer_fein));
        // Access the review page
        portal.visitActionRequiredERFormPage(submission.fineos_absence_id);
        // Deny the claim
        portal.respondToLeaveAdminRequest(false, true, false, false);
      });
    });
  });
});
