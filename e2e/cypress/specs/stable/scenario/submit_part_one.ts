import { fineos, portal } from "../../../actions";
import { getFineosBaseUrl } from "../../../config";

describe("Submit Part One of a claim, without documents, and then find in FINEOS", () => {
  const submit = it("As a claimant, I submit a claim through the portal (part one only)", () => {
    portal.before();

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

      // Submit Part 1
      portal.startClaim();
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
      fineos.before();
      cy.visit("/");

      cy.unstash<string>("claimNumber").then((claimNumber) => {
        fineos.visitClaim(claimNumber);
      });
    }
  );
});
