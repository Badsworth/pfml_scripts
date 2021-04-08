import * as portal from "../../../tests/common/actions/portal";
import { fineos } from "../../../tests/common/actions";
import { beforeFineos } from "../../../tests/common/before";
import { beforePortal } from "../../../tests/common/before";
import { getFineosBaseUrl } from "../../../config";

describe("Submit a bonding claim and adjucation approval - BHAP1", () => {
  const submit = it("As a claimant, I should be able to submit a claim (BHAP1) through the portal", () => {
    beforePortal();

    cy.task("generateClaim", "BGBM1").then((claim) => {
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
      cy.stash("credentials", credentials);
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
      portal.waitForClaimSubmission().then((data) => {
        cy.stashLog("claimNumber", data.fineos_absence_id);
        cy.stashLog("applicationId", data.application_id);
      });
      portal.submitPartsTwoThreeNoLeaveCert(paymentPreference);
    });
  });

  // Prepare for adjudication approval
  const adjudicate = it(
    "As a CSR (Savilinx), I should be able to Approve a BGBM1 claim submission",
    { baseUrl: getFineosBaseUrl() },
    () => {
      cy.dependsOnPreviousPass([submit]);
      beforeFineos();
      cy.visit("/");

      cy.unstash<string>("claimNumber").then((claimNumber) => {
        fineos.claimAdjudicationMailedDoc(claimNumber);
      });
    }
  );

  // Check Application card in portal for document uploaded in Fineos
  it("I should be able to see that a document has been uploaded in the portal", () => {
    cy.dependsOnPreviousPass([submit, adjudicate]);
    beforePortal();
    cy.unstash<Credentials>("credentials").then((credentials) => {
      portal.login(credentials);
      cy.unstash<string>("applicationId").then((application_id) => {
        portal.goToUploadCertificationPage(application_id);
        cy.contains("form", "Upload your documentation")
          .find("*[data-test='file-card']", { timeout: 30000 })
          .should("have.length", 1);
      });
    });
  });
});
