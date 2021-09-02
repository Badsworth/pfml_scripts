import { portal, fineos, fineosPages } from "../../../actions";
import { getLeaveAdminCredentials } from "../../../config";
import { assertValidClaim } from "../../../../src/util/typeUtils";
import { Submission } from "../../../../src/types";
describe("Create a new continuous leave, caring leave claim in FINEOS", () => {
  const fineosSubmission = it("Should be able to create a claim", () => {
    fineos.before();
    cy.visit("/");
    cy.task("generateClaim", "CDENY2").then((claim) => {
      cy.stash("claim", claim);
      assertValidClaim(claim.claim);
      fineosPages.ClaimantPage.visit(claim.claim.tax_identifier)
        .createNotification(claim.claim)
        .then((fineos_absence_id) => {
          cy.log(fineos_absence_id);
          cy.stash("submission", {
            fineos_absence_id: fineos_absence_id,
            timestamp_from: Date.now(),
          });
          fineosPages.ClaimPage.visit(fineos_absence_id)
            .documents((docs) => {
              claim.documents.forEach((document) =>
                docs
                  .uploadDocument(document.document_type)
                  .assertDocumentUploads(document.document_type)
              );
            })
            .tasks((taskPage) => {
              taskPage.add("ID Review");
              taskPage.add("Caring Certification Review");
            })
            .adjudicate((adjudication) => {
              adjudication.evidence((evidence) =>
                claim.documents.forEach(({ document_type }) =>
                  evidence.receive(document_type)
                )
              );
            })
            .tasks((taskPage) => {
              taskPage.close("ID Review");
              taskPage.close("Caring Certification Review");
            });
        });
    });
  });

  const employerDenial =
    it("Leave admin will submit ER denial for employee", () => {
      cy.dependsOnPreviousPass([fineosSubmission]);
      portal.before();
      cy.unstash<DehydratedClaim>("claim").then((claim) => {
        cy.unstash<Submission>("submission").then(({ fineos_absence_id }) => {
          assertValidClaim(claim.claim);
          portal.login(getLeaveAdminCredentials(claim.claim.employer_fein));
          portal.selectClaimFromEmployerDashboard(
            fineos_absence_id,
            "Review by"
          );
          portal.visitActionRequiredERFormPage(fineos_absence_id);
          portal.respondToLeaveAdminRequest(false, true, false, true);
        });
      });
    });

  it("CSR rep will deny claim", () => {
    cy.dependsOnPreviousPass([fineosSubmission, employerDenial]);
    fineos.before();
    cy.visit("/");
    cy.unstash<Submission>("submission").then(({ fineos_absence_id }) => {
      fineosPages.ClaimPage.visit(fineos_absence_id).deny(
        "Covered family relationship not established"
      );
    });
  });
});
