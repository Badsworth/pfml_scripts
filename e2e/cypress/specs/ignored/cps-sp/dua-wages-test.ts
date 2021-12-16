import { portal, fineos, fineosPages } from "../../../actions";
import { Submission } from "../../../../src/types";
import {assertValidClaim} from "../../../../src/util/typeUtils";
import {getLeaveAdminCredentials} from "../../../config";
import {FineosSecurityGroups} from "../../../../src/submission/fineos.pages";

Cypress.env({
  E2E_EMPLOYEES_FILE: "./employees/e2e-dua-wage.json",
  E2E_EMPLOYERS_FILE: "./employers/e2e-dua-wage.json",
});

describe("Submit a claim through Portal: Verify it creates an absence case in Fineos", () => {
  // claims.forEach((userPermission) => {
    const submissionTest =
      it("As a claimant, I should be able to submit a claim application through the portal", () => {
        portal.before();
        //@TODO adjust the generate claim for multiple different types and leave periods
        // Go to cypress.ts and adjust the CPS_SP by uncomment lines for what is needed to be tested.
        cy.task("generateClaim", "CPS_SP").then((claim) => {
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

    // const employerApproval =
    //   it("Leave admin will submit ER denial for employee", () => {
    //     cy.dependsOnPreviousPass([submissionTest]);
    //     portal.before();
    //     cy.unstash<DehydratedClaim>("claim").then((claim) => {
    //       cy.unstash<Submission>("submission").then(({fineos_absence_id}) => {
    //         assertValidClaim(claim.claim);
    //         portal.login(getLeaveAdminCredentials(claim.claim.employer_fein));
    //         portal.selectClaimFromEmployerDashboard(fineos_absence_id);
    //         portal.visitActionRequiredERFormPage(fineos_absence_id);
    //         portal.respondToLeaveAdminRequest(false, true, true, true);
    //       });
    //     });
    //   });

    //Fineos check absence case here.
    it("Should check the claim in Fineos.", () => {
      cy.dependsOnPreviousPass([submissionTest]);
      fineos.before();
      cy.unstash<DehydratedClaim>("claim").then((claim) => {
        cy.unstash<Submission>("submission").then((submission) => {
          const claimPage = fineosPages.ClaimPage.visit(
            submission.fineos_absence_id
          );
          claimPage.shouldHaveStatus("Eligibility", "Met");
          // claimPage.adjudicate((adjudicate) => {
          //   adjudicate.evidence((evidence) => {
          //     claim.documents.forEach((document) => {
          //       evidence.receive(document.document_type);
          //     });
          //   });
          //   adjudicate.certificationPeriods((cert) => cert.prefill());
          //   adjudicate.acceptLeavePlan();
          // });
          // claimPage.outstandingRequirements((outstandingRequirements) => {
          //   outstandingRequirements.complete(
          //     "Received",
          //     "Complete Employer Confirmation",
          //     true
          //   );
          // });
          // claimPage.approve();
        });
      });
    });
  // });
});

