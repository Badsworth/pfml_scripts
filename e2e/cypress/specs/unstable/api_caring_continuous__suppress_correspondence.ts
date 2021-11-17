import { fineos, fineosPages } from "../../actions";
import { Submission } from "../../../src/types";

describe("Create a new caring leave claim in FINEOS and Suppress Correspondence check", () => {

  const notification =
    it("Create an absence case for the Suppress Correspondence", () => {
      fineos.before();
      cy.task("generateClaim", "HIST_CASE").then((claim) => {
        cy.task("submitClaimToAPI", claim).then((res) => {
          cy.stash("claim", claim.claim);
          cy.stash("submission", {
            application_id: res.application_id,
            fineos_absence_id: res.fineos_absence_id,
            timestamp_from: Date.now(),
          });
          fineosPages.ClaimPage.visit(
            res.fineos_absence_id
          )
        });
      });
    });

  it("Check to see if the Suppress Correspondence is available in the Absence Case",
    {retries: 0},
    () => {
      cy.dependsOnPreviousPass([notification]);
      fineos.before();
      cy.unstash<Submission>("submission").then((submission) => {
        fineosPages.ClaimPage.visit(submission.fineos_absence_id)
          .removeSuppressCorrespondence()
          .documents((docsPage) => {
            docsPage.assertDocumentExists("Notification Suppression Disabled");
          });
      });
    });
});
