import { portal, fineos, fineosPages } from "../../actions";
import { getFineosBaseUrl, getLeaveAdminCredentials } from "../../config";
import { assertValidClaim } from "../../../src/util/typeUtils";
import { Submission } from "../../../src/types";

describe("Submit a claim through Portal: Verify it creates an absence case in Fineos", () => {
  const fineosSubmission =
    it("As a claimant, I should be able to submit a claim application through the portal", () => {
      portal.before();
      cy.task("generateClaim", "CDENY2").then((claim) => {
        cy.stash("claim", claim);
        const application: ApplicationRequestBody = claim.claim;
        const paymentPreference = claim.paymentPreference;
        portal.loginClaimant();
        portal.goToDashboardFromApplicationsPage();

        // Submit Claim
        portal.startClaim();
        portal.submitClaimPartOne(application);
        portal.waitForClaimSubmission().then((data) => {
          cy.stash("submission", {
            application_id: data.application_id,
            fineos_absence_id: data.fineos_absence_id,
            timestamp_from: Date.now(),
          });
        });
        portal.submitClaimPartsTwoThree(application, paymentPreference);
      });
    });

  // const employerDenial =
  //   it("Leave admin will submit ER denial for employee", () => {
  //     cy.dependsOnPreviousPass([fineosSubmission]);
  //     portal.before();
  //     cy.unstash<DehydratedClaim>("claim").then((claim) => {
  //       cy.unstash<Submission>("submission").then(({ fineos_absence_id }) => {
  //         assertValidClaim(claim.claim);
  //         portal.login(getLeaveAdminCredentials(claim.claim.employer_fein));
  //         portal.selectClaimFromEmployerDashboard(fineos_absence_id, "--");
  //         portal.visitActionRequiredERFormPage(fineos_absence_id);
  //         portal.respondToLeaveAdminRequest(false, true, false, true);
  //       });
  //     });
  //   });

  it("CSR will deny claim", { baseUrl: getFineosBaseUrl() }, () => {
    cy.dependsOnPreviousPass([fineosSubmission]);
    fineos.before();
    cy.visit("/");
    cy.unstash<Submission>("submission").then(({ fineos_absence_id }) => {
      fineosPages.ClaimPage.visit(fineos_absence_id)
        .deny("Covered family relationship not established")
        .triggerNotice("Leave Request Declined")
    });
  });

  it(
    "CSR will process a decision change",
    { baseUrl: getFineosBaseUrl() },
    () => {
      cy.dependsOnPreviousPass([fineosSubmission]);
      fineos.before();
      cy.visit("/");
      cy.unstash<Submission>("submission").then(({ fineos_absence_id }) => {
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
      });
    }
  );
});
