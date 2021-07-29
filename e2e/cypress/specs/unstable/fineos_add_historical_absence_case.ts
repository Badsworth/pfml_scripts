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
      }).then((res) => {
        fineos.before();
        cy.visit("/");
        cy.stash("claim", claim.claim);
        cy.stash("submission", {
          application_id: res.application_id,
          fineos_absence_id: res.fineos_absence_id,
          timestamp_from: Date.now(),
        });
        fineosPages.ClaimPage.visit(res.fineos_absence_id);
        fineos.addHistoricalAbsenceCase();
      });
    });
  });
});
