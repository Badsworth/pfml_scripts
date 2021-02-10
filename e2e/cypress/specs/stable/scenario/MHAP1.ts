import * as portal from "../../../tests/common/actions/portal";
import { fineos } from "../../../tests/common/actions";
import { beforeFineos } from "../../../tests/common/before";
import { beforePortal } from "../../../tests/common/before";
import { getFineosBaseUrl } from "../../../config";
import { Submission } from "../../../../src/types";

describe("Submit a medical claim and adjucation approval - MHAP1", () => {
  it("As a claimant, I should be able to submit a Medical Leave claim (MHAP1) through the portal", () => {
    beforePortal();

    cy.task("generateClaim", {
      claimType: "MHAP1",
      employeeType: "financially eligible",
    }).then((claim: SimulationClaim) => {
      if (!claim) {
        throw new Error("Claim Was Not Generated");
      }
      cy.log("generated claim", claim.claim);
      const application: ApplicationRequestBody = claim.claim;
      const paymentPreference = claim.paymentPreference;

      const credentials: Credentials = {
        username: Cypress.env("E2E_PORTAL_USERNAME"),
        password: Cypress.env("E2E_PORTAL_PASSWORD"),
      };
      portal.login(credentials);
      portal.goToDashboardFromApplicationsPage();

      // Continue Creating Claim
      portal.startClaim();
      portal.onPage("start");
      portal.agreeToStart();
      portal.hasClaimId();
      portal.onPage("checklist");

      // Submit Claim
      portal.submitClaimPartOne(application);
      cy.wait("@submitClaimResponse").then((xhr) => {
        if (!xhr.response || !xhr.response.body) {
          throw new Error("No response body detected");
        }
        const body =
          typeof xhr.response.body === "string"
            ? JSON.parse(xhr.response.body)
            : xhr.response.body;
        cy.stash("submission", {
          application_id: body.data.application_id,
          fineos_absence_id: body.data.fineos_absence_id,
          timestamp_from: Date.now(),
        });
      });
      portal.submitClaimPartsTwoThree(application, paymentPreference);
    });
  });

  // Prepare for adjudication approval
  it(
    "As a CSR (Savilinx), I should be able to Approve a MHAP1 claim submission",
    { baseUrl: getFineosBaseUrl() },
    () => {
      beforeFineos();
      cy.visit("/");

      cy.unstash<Submission>("submission").then((submission) => {
        fineos.claimAdjudicationFlow(submission.fineos_absence_id);
      });
    }
  );
});
