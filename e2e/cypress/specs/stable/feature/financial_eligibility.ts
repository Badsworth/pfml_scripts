import { getFineosBaseUrl } from "../../../config";
import { beforeFineos } from "../../../tests/common/before";
import { fineos } from "../../../tests/common/actions";
import { Submission } from "../../../../src/types";

describe("Financial Eligibility Calculation", () => {
  it(
    "Claims for a financially eligible claimant should be marked met.",
    { baseUrl: getFineosBaseUrl() },
    () => {
      beforeFineos();
      cy.visit("/");

      cy.task("generateClaim", {
        claimType: "BHAP1",
        employeeType: "financially eligible",
      }).then((claim: SimulationClaim) => {
        cy.task("submitClaimToAPI", claim).as("submission");
      });

      // Request for additional Info in Fineos
      cy.get<Submission>("@submission").then((submission) => {
        fineos.visitClaim(submission.fineos_absence_id);
        fineos.assertClaimFinancialEligibility(true);
      });
    }
  );

  it(
    "Claims for a financially eligible claimant should be marked not met.",
    { baseUrl: getFineosBaseUrl() },
    () => {
      beforeFineos();
      cy.visit("/");

      cy.task("generateClaim", {
        claimType: "BHAP1",
        employeeType: "financially ineligible",
      }).then((claim: SimulationClaim) => {
        cy.task("submitClaimToAPI", claim).as("submission");
      });

      // Request for additional Info in Fineos
      cy.get<Submission>("@submission").then((submission) => {
        fineos.visitClaim(submission.fineos_absence_id);
        fineos.assertClaimFinancialEligibility(false);
      });
    }
  );
});
