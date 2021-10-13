import { fineos, fineosPages, portal } from "../../../actions";
import { Submission } from "../../../../src/types";
import { config } from "../../../actions/common";

describe("Create a new caring leave claim in FINEOS and add Historical Absence case. Then withdraw the Absence Case", () => {
  after(() => {
    portal.deleteDownloadsFolder();
  });

  it("Create historical absence case within Absence Case", () => {
    cy.task("generateClaim", "HIST_CASE").then((claim) => {
      cy.task("submitClaimToAPI", claim).then((res) => {
        fineos.before();
        cy.stash("claim", claim.claim);
        cy.stash("submission", {
          application_id: res.application_id,
          fineos_absence_id: res.fineos_absence_id,
          timestamp_from: Date.now(),
        });
        fineosPages.ClaimPage.visit(
          res.fineos_absence_id
        ).addHistoricalAbsenceCase();
      });
    });
  });

  const withdraw =
    it('Withdraw a claim in Fineos and check for a "Pending Application Withdrawn" notice', () => {
      fineos.before();
      cy.unstash<Submission>("submission").then((submission) => {
        const claimPage = fineosPages.ClaimPage.visit(
          submission.fineos_absence_id
        );
        claimPage.withdraw();
        claimPage.triggerNotice("Leave Request Withdrawn");
        claimPage.documents((docsPage) => {
          docsPage.assertDocumentExists("Pending Application Withdrawn");
        });
      });
    });

  it("Produces a withdrawn notice, avilable for download", () => {
    if (config("HAS_WITHDRAWN_NOTICE") === "true") {
      cy.dependsOnPreviousPass([withdraw]);
      portal.before();
      cy.visit("/");
      portal.loginClaimant();
      cy.unstash<Submission>("submission").then((submission) => {
        portal.claimantGoToClaimStatus(submission.fineos_absence_id);
        portal.claimantAssertClaimStatus([
          { leave: "Care for a Family Member", status: "Withdrawn" },
        ]);
        cy.findByText("Pending Application Withdrawn (PDF)")
          .should("be.visible")
          .click();
        portal.downloadLegalNotice(submission.fineos_absence_id);
      });
    }
  });
});
