import { fineos, fineosPages, portal } from "../../actions";
import { getFineosBaseUrl, getLeaveAdminCredentials } from "../../config";

import { Submission } from "../../../src/types";
import { assertValidClaim } from "../../../src/util/typeUtils";
import { config } from "../../actions/common";

describe("Create a new continuous leave, caring leave claim in FINEOS", () => {

  const credentials: Credentials = {
    username: Cypress.env("E2E_PORTAL_USERNAME"),
    password: Cypress.env("E2E_PORTAL_PASSWORD"),
  };
  
  // const fineosSubmission = 
  //   it("Create a claim with a Denial ER through the API", { baseUrl: getFineosBaseUrl() }, () => {
  //     cy.task("generateClaim", "CDENY2").then((claim) => {
  //       cy.task("submitClaimToAPI", {
  //         ...claim,
  //         credentials,
  //       }).then((res) => {
  //         fineos.before();
  //         cy.visit("/");
  //         cy.stash("claim", claim.claim);
  //         cy.stash("submission", {
  //           application_id: res.application_id,
  //           fineos_absence_id: res.fineos_absence_id,
  //           timestamp_from: Date.now(),
  //         });
  //         fineosPages.ClaimPage.visit(res.fineos_absence_id)
  //         .adjudicate((adjudication) => {
  //           adjudication.evidence((evidence) =>
  //             claim.documents.forEach(({ document_type }) =>
  //               evidence.receive(document_type)
  //             )
  //           );
  //         })
  //       });
  //     });
  //   });
  const fineos_absence_id = "NTN-37921-ABS-01"
  it("CSR will deny claim", { baseUrl: getFineosBaseUrl() }, () => {
    // cy.dependsOnPreviousPass([fineosSubmission]);
    fineos.before();
    cy.visit("/");
    // cy.unstash<Submission>("submission").then(({ fineos_absence_id }) => {
      fineosPages.ClaimPage.visit(fineos_absence_id)
          .deny("Covered family relationship not established")
          .triggerNotice("Leave Request Declined")    
    // });
  });

  it(
    "CSR will process a decision change",
    { baseUrl: getFineosBaseUrl() },
    () => {
      // cy.dependsOnPreviousPass([fineosSubmission]);
      fineos.before();
      cy.visit("/");
      // cy.unstash<Submission>("submission").then(({ fineos_absence_id }) => {
        const claimPage = fineosPages.ClaimPage.visit(fineos_absence_id);
        claimPage.addAppeal();
        claimPage.triggerNotice("SOM Generate Appeals Notice");
        claimPage.appealDocuments((docPage) => {
          docPage.assertDocumentExists("Appeal Acknowledgment");
        });
        claimPage.appealTasks((tasks) => {
          tasks.closeAppealReview();
          tasks.close("Schedule Hearing");
          tasks.close("Conduct Hearing");
          tasks.closeConductHearing();
          tasks.assertTaskExists("Send Decision Notice");
        });
        claimPage.appealDocuments((docPage) => {
          docPage.uploadDocument("Appeal Notice - Claim Decision Changed");
          docPage.assertDocumentUploads(
            "Appeal Notice - Claim Decision Changed"
          );
        });
      // });
    }
  );

  // it(
  //   "Should generate a legal notice (Approval) that the claimant can view",
  //   { retries: 0 },
  //   () => {
  //     cy.dependsOnPreviousPass([submit]);
  //     portal.before({
  //       claimantShowStatusPage: config("HAS_CLAIMANT_STATUS_PAGE") === "true",
  //     });
  //     portal.loginClaimant();
  //     cy.unstash<Submission>("submission").then((submission) => {
  //       // Wait for the legal document to arrive.
  //       if (config("HAS_CLAIMANT_STATUS_PAGE") .3=== "true") {
  //         portal.claimantGoToClaimStatus(submission.fineos_absence_id);
  //         portal.claimantAssertClaimStatus([
  //           { leave: "Child Bonding", status: "Approved" },
  //         ]);
  //         // @todo: uncomment lines below once, doc download is supported
  //         // cy.findByText("Approval notice (PDF)").should("be.visible").click();
  //         // portal.downloadLegalNotice(submission.fineos_absence_id);
  //       } else {
  //         // @todo: remove once claimant status is deployed to all envs
  //         cy.task(
  //           "waitForClaimDocuments",
  //           {
  //             credentials: getClaimantCredentials(),
  //             application_id: submission.application_id,
  //             document_type: "Approval Notice",
  //           },
  //           { timeout: 30000 }
  //         );
  //         cy.contains("article", submission.fineos_absence_id).within(() => {
  //           cy.findByText("Approval notice (PDF)").should("be.visible").click();
  //         });
  //         portal.downloadLegalNotice(submission.fineos_absence_id);
  //       }
  //     });
  //   }
  // );
});