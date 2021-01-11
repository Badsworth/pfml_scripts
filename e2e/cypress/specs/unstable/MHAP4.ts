import * as portal from "../../tests/common/actions/portal";
import { fineos } from "../../tests/common/actions";
import { beforeFineos } from "../../tests/common/before";
import { beforePortal } from "../../tests/common/before";
import { getLeaveAdminCredentials, getFineosBaseUrl } from "../../config";
import { ApplicationResponse } from "../../../src/api";
import { Submission } from "../../../src/types";

describe("Submitting a Medical pregnancy claim and adding bonding leave in Fineos", () => {
  it("Create a financially eligible claim (MHAP4) in which an employer will respond", () => {
    beforePortal();

    cy.task("generateClaim", {
      claimType: "MHAP4",
      employeeType: "financially eligible",
    }).then((claim: SimulationClaim) => {
      if (!claim) {
        throw new Error("Claim Was Not Generated");
      }
      cy.log("generated claim", claim.claim);

      const credentials: Credentials = {
        username: Cypress.env("E2E_PORTAL_USERNAME"),
        password: Cypress.env("E2E_PORTAL_PASSWORD"),
      };

      cy.stash("claim", claim.claim);
      cy.task("submitClaimToAPI", {
        ...claim,
        credentials,
      } as SimulationClaim).then((response: ApplicationResponse) => {
        console.log(response);
        cy.stash("submission", {
          application_id: response.application_id,
          fineos_absence_id: response.fineos_absence_id,
          timestamp_from: Date.now(),
        });
        // Complete Employer Response
        if (typeof claim.claim.employer_fein !== "string") {
          throw new Error("Claim must include employer FEIN");
        }
        if (typeof response.fineos_absence_id !== "string") {
          throw new Error("Response must include FINEOS absence ID");
        }

        portal.login(getLeaveAdminCredentials(claim.claim.employer_fein));
        portal.respondToLeaveAdminRequest(
          response.fineos_absence_id,
          false,
          true,
          true
        );
      });
    });
  });

  // Check for ER and approval claim in Fineos
  it(
    "In Fineos, complete an Adjudication Approval along w/adding Bonding Leave",
    { baseUrl: getFineosBaseUrl() },
    () => {
      beforeFineos();
      cy.unstash<Submission>("submission").then((submission) => {
        cy.visit("/");
        fineos.claimAdjudicationFlow(submission.fineos_absence_id, true);
        fineos.addBondingLeaveFlow(submission.timestamp_from);
        cy.wait(200);
      });
    }
  );
});
