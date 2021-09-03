import { fineos, fineosPages, portal } from "../../actions";

import { Submission } from "../../../src/types";
import { config } from "../../actions/common";

describe("Create a new continuous medical leave claim in FINEOS and add Historical Absence case. Then withdraw the Absence Case", () => {
  const credentials: Credentials = {
    username: config("PORTAL_USERNAME"),
    password: config("PORTAL_PASSWORD"),
  };

  const submit = it("Create historical absence case within Absence Case", () => {
    cy.task("generateClaim", "HIST_CASE").then((claim) => {
      cy.task("submitClaimToAPI", {
        ...claim,
        credentials,
      }).then((res) => {
        fineos.before();
        cy.visit("/");
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

  it(
    "Should generate a legal notice (Withdrawal) that the claimant can view",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass([submit]);
      portal.before();
      cy.visit("/");
      portal.login(credentials);
      cy.unstash<Submission>("submission").then((submission) => {
        // Wait for the legal document to arrive.
        cy.task(
          "waitForClaimDocuments",
          {
            credentials: credentials,
            application_id: submission.application_id,
            document_type: "Pending Application Withdrawn",
          },
          { timeout: 30000 }
        );

        cy.visit("/applications");
        cy.contains("article", submission.fineos_absence_id).within(() => {
          cy.findByText("Pending Application Withdrawn (PDF)").should("be.visible").click();
        });
        portal.downloadLegalNotice(submission.fineos_absence_id);
      });
    }
  );
});
