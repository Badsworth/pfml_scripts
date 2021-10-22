import { fineos, portal } from "../../../actions";
import { assertValidClaim } from "../../../../src/util/typeUtils";
import { ClaimantPage, ClaimPage } from "../../../actions/fineos.pages";
import { Submission } from "../../../../src/types";
describe("Create a new continuous leave, military caregiver claim in FINEOS", () => {
  const claimSubmission = it("Should be able to create a claim", () => {
    fineos.before();
    cy.visit("/");
    cy.task("generateClaim", "MIL_EXI").then((claim) => {
      assertValidClaim(claim.claim);
      cy.stash("claim", claim);

      ClaimantPage.visit(claim.claim.tax_identifier)
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

  it("LA can review and approve the claim", () => {
    cy.dependsOnPreviousPass([claimSubmission]);
    portal.before();
    cy.unstash<DehydratedClaim>("claim").then(({ claim }) => {
      cy.unstash<Submission>("submission").then((submission) => {
        assertValidClaim(claim);
        portal.loginLeaveAdmin(claim.employer_fein);
        // Access the review page
        portal.visitActionRequiredERFormPage(submission.fineos_absence_id);
        // Deny the claim
        portal.assertLeaveType("Active duty");
        portal.respondToLeaveAdminRequest(false, true, false, false);
      });
    });
  });
});
