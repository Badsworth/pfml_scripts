import { fineos, portal, fineosPages } from "../../../actions";
import { getFineosBaseUrl } from "../../../config";
import { ApplicationResponse } from "../../../../src/api";
import { config } from "../../../actions/common";

describe("Withdraw Notification and Notice", () => {
  after(() => {
    portal.deleteDownloadsFolder();
  });

  const credentials: Credentials = {
    username: config("PORTAL_USERNAME"),
    password: config("PORTAL_PASSWORD"),
  };

  it(
    "Given a withdraw claim in Fineos",
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
          const claimPage = fineosPages.ClaimPage.visit(
            responseData.fineos_absence_id
          );
          claimPage.tasks((tasks) => {
            tasks.assertTaskExists("Medical Certification Review");
            tasks.close("Medical Certification Review");
            tasks.assertTaskExists("ID Review");
            tasks.close("ID Review");
          });
          claimPage.withdraw();
          claimPage.triggerNotice("Pending Application Withdrawn");
          claimPage.documents((docsPage) => {
            docsPage.assertDocumentExists("Pending Application Withdrawn");
          });
        });
      });
    }
  );
});
