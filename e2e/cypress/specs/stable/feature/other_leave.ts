import { fineos, portal } from "../../../tests/common/actions";
import {
  bailIfThisTestFails,
  beforeFineos,
} from "../../../tests/common/before";
import { beforePortal } from "../../../tests/common/before";
import { getFineosBaseUrl } from "../../../config";
import { Submission } from "../../../../src/types";

describe("Submit a bonding claim with other income and other leave - BHAP1", () => {
  it("As a claimant, I submit a BHAP1 claim with other leave and other income through the portal", () => {
    beforePortal();
    bailIfThisTestFails();

    cy.task("generateClaim", {
      claimType: "BHAP1",
      employeeType: "financially eligible",
    }).then((claim: SimulationClaim) => {
      if (!claim) {
        throw new Error("Claim Was Not Generated");
      }
      cy.stash("claim", claim);
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
      portal.submitClaimPartOne(application, true);
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
  // Check for Other Leave Document
  it(
    "In Fineos, check for Other Leave E-Form",
    { baseUrl: getFineosBaseUrl() },
    () => {
      beforeFineos();
      cy.unstash<Submission>("submission").then((submission) => {
        cy.visit("/");
        fineos.findOtherLeaveEForm(submission.fineos_absence_id);
      });
    }
  );
});
