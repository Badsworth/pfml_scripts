import { fineos } from "../../../tests/common/actions";
import { beforeFineos } from "../../../tests/common/before";
import { getFineosBaseUrl } from "../../../config";

describe("Generate and submit Claim via the API and check Payment Data in Fineos", () => {
  it(
    "Create a financially eligible claim and confirm info in Payment Preference",
    { baseUrl: getFineosBaseUrl() },
    () => {
      beforeFineos();
      cy.visit("/");

      const credentials: Credentials = {
        username: Cypress.env("E2E_PORTAL_USERNAME"),
        password: Cypress.env("E2E_PORTAL_PASSWORD"),
      };

      cy.task("generateClaim", {
        claimType: "BHAP1",
        employeeType: "financially eligible",
      }).then((claim: SimulationClaim) => {
        cy.wrap(claim).as("claim");
        cy.task("submitClaimToAPI", {
          ...claim,
          credentials,
        } as SimulationClaim).then((response) => {
          console.log(response);
        });
      });

      // Request for additional Info in Fineos
      cy.get<SimulationClaim>("@claim").then((claim) => {
        fineos.checkPaymentPreference(claim);
      });
    }
  );
});
