import { fineos, portal, fineosPages } from "../../actions";
import { getFineosBaseUrl } from "../../config";
import { ApplicationResponse } from "../../../src/api";
import { config } from "../../actions/common";
import { Submission } from "../../../src/types";

describe("Withdraw Notification and Notice", () => {
  after(() => {
    portal.deleteDownloadsFolder();
  });

  const credentials: Credentials = {
    username: config("PORTAL_USERNAME"),
    password: config("PORTAL_PASSWORD"),
  };

  it(
    "Submit a claim to Fineos through the API",
    { baseUrl: getFineosBaseUrl() },
    () => {
      fineos.before();
      cy.visit("/");
      cy.task("generateClaim", "WDCLAIM").then((claim) => {
        cy.task("submitClaimToAPI", {
          ...claim,
          credentials,
        }).then((responseData: ApplicationResponse) => {
          if (!responseData.fineos_absence_id) {
            throw new Error("FINEOS ID must be specified");
          }
          cy.stash("claim", claim.claim);
          cy.stash("submission", {
            application_id: responseData.application_id,
            fineos_absence_id: responseData.fineos_absence_id,
            timestamp_from: Date.now(),
          });
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
