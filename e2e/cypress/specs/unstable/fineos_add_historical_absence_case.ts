import { fineos, fineosPages } from "../../actions";
import { getFineosBaseUrl } from "../../config";
import { config } from "../../actions/common";

describe("Create a new continuous leave, medical leave claim in FINEOS and adding Historical Absence case", () => {
  const credentials: Credentials = {
    username: config("PORTAL_USERNAME"),
    password: config("PORTAL_PASSWORD"),
  };

  it("Create historical absence case", { baseUrl: getFineosBaseUrl() }, () => {
    cy.task("generateClaim", "HIST_CASE").then((claim) => {
      cy.task("submitClaimToAPI", {
        ...claim,
        credentials,
      }).then((responseData: ApplicationResponse) => {
        fineos.before();
        cy.visit("/");
        if (!responseData.fineos_absence_id) {
          throw new Error("FINEOS ID must be specified");
        }
        cy.stash("claim", claim.claim);
        cy.stash("submission", {
          application_id: responseData.application_id,
          fineos_absence_id: responseData.fineos_absence_id,
          timestamp_from: Date.now(),
        });
        fineosPages.ClaimPage.visit(responseData.fineos_absence_id);
        fineos.addHistoricalAbsenceCase();
      });
    });
  });
});
