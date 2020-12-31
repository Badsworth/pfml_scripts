import { getFineosBaseUrl } from "../../../config";
import { beforeFineos } from "../../../tests/common/before";
import { fineos } from "../../../tests/common/actions";
import { Submission } from "../../../../src/types";

describe("Submit a <Scenario> claim directly to API and check for RMV Identification Status", () => {
  it(
    "I submit a claim via the API and check Fineos RMV status as fraud",
    { baseUrl: getFineosBaseUrl() },
    () => {
      beforeFineos();
      cy.visit("/");

      cy.task("generateClaim", {
        claimType: "BHAP11ID",
        employeeType: "financially eligible",
      }).then((claim: SimulationClaim) => {
        cy.task("submitClaimToAPI", claim).as("submission");
      });

      // Confirm Proper RMV Status
      cy.get<Submission>("@submission").then((submission) => {
        fineos.visitClaim(submission.fineos_absence_id);
        fineos.confirmRMVStatus("fraud");
      });
    }
  );
  it(
    "I submit a claim via the API and check Fineos RMV status as invalid",
    { baseUrl: getFineosBaseUrl() },
    () => {
      beforeFineos();
      cy.visit("/");

      cy.task("generateClaim", {
        claimType: "BHAP12ID",
        employeeType: "financially eligible",
      }).then((claim: SimulationClaim) => {
        cy.task("submitClaimToAPI", claim).as("submission");
      });

      // Confirm Proper RMV Status
      cy.get<Submission>("@submission").then((submission) => {
        fineos.visitClaim(submission.fineos_absence_id);
        fineos.confirmRMVStatus("invalid");
      });
    }
  );

  it(
    "I submit a claim via the API and check Fineos RMV status as valid",
    { baseUrl: getFineosBaseUrl() },
    () => {
      beforeFineos();
      cy.visit("/");

      cy.task("generateClaim", {
        claimType: "BHAP10ID",
        employeeType: "financially eligible",
      }).then((claim: SimulationClaim) => {
        cy.task("submitClaimToAPI", claim).as("submission");
      });

      // Confirm Proper RMV Status
      cy.get<Submission>("@submission").then((submission) => {
        fineos.visitClaim(submission.fineos_absence_id);
        fineos.confirmRMVStatus("valid");
      });
    }
  );

  it(
    "I submit a claim via the API and check Fineos RMV status as mismatch",
    { baseUrl: getFineosBaseUrl() },
    () => {
      beforeFineos();
      cy.visit("/");

      cy.task("generateClaim", {
        claimType: "BHAP13ID",
        employeeType: "financially eligible",
      }).then((claim: SimulationClaim) => {
        cy.task("submitClaimToAPI", claim).as("submission");
      });

      // Confirm Proper RMV Status
      cy.get<Submission>("@submission").then((submission) => {
        fineos.visitClaim(submission.fineos_absence_id);
        fineos.confirmRMVStatus("mismatch");
      });
    }
  );
});
