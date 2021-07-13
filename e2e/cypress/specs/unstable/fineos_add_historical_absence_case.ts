import { fineos, fineosPages } from "../../actions";
import { extractLeavePeriod } from "../../../src/util/claims";
import { getFineosBaseUrl } from "../../config";
import { assertValidClaim } from "../../../src/util/typeUtils";
import {addHistoricalAbsenceCase} from "../../actions/fineos";
import { config } from "../../actions/common";

describe("Create a new continuous leave, medical leave claim in FINEOS and adding Historical Absence case", () => {
  
  const credentials: Credentials = {
    username: config("PORTAL_USERNAME"),
    password: config("PORTAL_PASSWORD"),
  };

  it(
    "Create historical absence case",
    { baseUrl: getFineosBaseUrl() },
    () => {
      fineos.before();
      cy.visit("/");

      cy.task("generateClaim", "HIST_CASE").then((claim) => {
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
          const page = fineosPages.ClaimPage.visit(
            responseData.fineos_absence_id
          );
          fineos.addHistoricalAbsenceCase(responseData.fineos_absence_id);
        });
      });
    }
  )
});

      