import { fineos, fineosPages, portal } from "../../../actions";
import { getLeaveAdminCredentials } from "../../../config";
import { assertValidClaim } from "../../../../src/util/typeUtils";
import { ClaimPage } from "../../../actions/fineos.pages";
import { Submission } from "../../../../src/types";

describe("Create a new continuous leave, military caregiver claim in FINEOS", () => {
  const claimSubmission = it("Should be able to create a claim", () => {
    fineos.before();
    cy.task("generateClaim", "MIL_RED").then((claim) => {
      assertValidClaim(claim.claim);
      cy.stash("claim", claim);

      fineosPages.ClaimantPage.visit(claim.claim.tax_identifier)
        .createNotification(claim.claim)
        .then((fineos_absence_id) => {
          cy.log(fineos_absence_id);
          cy.stash("submission", { fineos_absence_id });

          ClaimPage.visit(fineos_absence_id).adjudicate((adjudication) => {
            adjudication.evidence((evidence) => {
              claim.documents.forEach((doc) =>
                evidence.receive(doc.document_type)
              );
            });
          });
        });
    });
  });

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
