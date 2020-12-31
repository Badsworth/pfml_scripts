import { fineos, portal } from "../../../tests/common/actions";
import { beforeFineos } from "../../../tests/common/before";
import { beforePortal } from "../../../tests/common/before";
import { getFineosBaseUrl } from "../../../config";
import { ApplicationResponse } from "../../../../src/api";
import { Submission } from "../../../../src/types";

describe("Upload a document in FINEOS and see it has been uploaded in the portal", () => {
  it("Register Claimant and submit claim w/o documents directly to the API", () => {
    beforePortal();
    cy.visit("/");

    // Generate Creds for Registration/Login - submit claim via API
    cy.task("generateCredentials", false).then((credentials) => {
      cy.stash("credentials", credentials);
      cy.task("registerClaimant", credentials).then(() => {
        cy.task("generateClaim", {
          claimType: "BGBM3",
          employeeType: "financially eligible",
        }).then((claim: SimulationClaim) => {
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
          });
        });
      });
    });
  });

  // Upload ID document in Fineos
  it(
    "As a CSR (Savilinx), I upload an MA ID document to a claim",
    { baseUrl: getFineosBaseUrl() },
    () => {
      beforeFineos();
      cy.unstash<Submission>("submission").then((submission) => {
        cy.visit("/");
        fineos.uploadIDdoc(submission.fineos_absence_id);
      });
    }
  );

  // Check Application card for document uploaded in Fineos
  it("I should be able to see that a document has been uploaded in the portal", () => {
    beforePortal();
    cy.unstash<Credentials>("credentials").then((credentials) => {
      portal.login(credentials);
      cy.unstash<Submission>("submission").then((submission) => {
        portal.goToIdUploadPage(submission.application_id);
        cy.contains(
          "form",
          "Upload your Massachusetts driver’s license or ID card"
        )
          .find("h3")
          .should("have.length", 1);
      });
    });
  });
});
