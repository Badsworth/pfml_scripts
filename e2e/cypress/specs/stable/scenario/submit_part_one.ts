import * as portal from "../../../tests/common/actions/portal";
import { fineos } from "../../../tests/common/actions";
import { beforeFineos } from "../../../tests/common/before";
import { beforePortal } from "../../../tests/common/before";
import { getFineosBaseUrl } from "../../../config";

describe("Submit Part One of a claim, without documents, and then find in FINEOS", () => {
  const submit = it("As a claimant, I submit a claim through the portal (part one only)", () => {
    beforePortal();

    cy.task("generateClaim", "MHAP1").then((claim) => {
      if (!claim) {
        throw new Error("Claim Was Not Generated");
      }
      cy.log("generated claim", claim.claim);
      const application: ApplicationRequestBody = claim.claim;

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

      // Submit Part 1
      portal.submitClaimPartOne(application);
      portal.waitForClaimSubmission().then((data) => {
        cy.stashLog("claimNumber", data.fineos_absence_id);
        cy.stashLog("applicationId", data.application_id);
      });
    });
  });

  // Prepare for adjudication approval
  it(
    "As a CSR (Savilinx), I should be able to Approve a MHAP1 claim submission",
    { baseUrl: getFineosBaseUrl() },
    () => {
      cy.dependsOnPreviousPass([submit]);
      beforeFineos();
      cy.visit("/");

      cy.unstash<string>("claimNumber").then((claimNumber) => {
        fineos.visitClaim(claimNumber);
      });
    }
  );
});
