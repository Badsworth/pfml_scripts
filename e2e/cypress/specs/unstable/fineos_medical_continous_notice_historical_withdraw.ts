import { fineos, fineosPages } from "../../actions";
import { getFineosBaseUrl } from "../../config";
import { config } from "../../actions/common";
import { Submission } from "../../../src/types";

describe("Create a new continuous medical leave claim in FINEOS and add Historical Absence case. Then withdraw the Absence Case", () => {
  const credentials: Credentials = {
    username: config("PORTAL_USERNAME"),
    password: config("PORTAL_PASSWORD"),
  };

  it(
    "Create historical absence case within Absence Case",
    { baseUrl: getFineosBaseUrl() },
    () => {
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
    }
  );

  it(
    'Withdraw a claim in Fineos and check for a "Pending Application Withdrawn" notice',
    { baseUrl: getFineosBaseUrl() },
    () => {
      fineos.before();
      cy.visit("/");

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
    }
  );
});
