import { fineos, fineosPages } from "../../actions";
import {assertValidClaim} from "../../../src/util/typeUtils";


describe("Submit a claim through FINEOS with OrgUnit included", () => {
  const fineosIntake = it("Should be able to create a claim", () => {
    fineos.before();
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
          fineosPages.ClaimPage.visit(fineos_absence_id).adjudicate(
            (adjudication) => {
              adjudication.evidence((evidence) =>
                claim.documents.forEach(({ document_type }) =>
                  evidence.receive(document_type)
                )
              );
            }
          );
        });
    });
  });


})
