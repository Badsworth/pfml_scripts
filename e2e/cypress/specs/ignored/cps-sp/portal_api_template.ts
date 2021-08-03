import { fineos, fineosPages, portal } from "../../../actions";
import { getFineosBaseUrl } from "../../../config";
import { Submission } from "../../../../src/types";
import { config } from "../../../actions/common";

//Portal and API call to submit claim
describe("Submit a claim through Portal: Verify it creates an absence case in Fineos", () => {
  const submissionTest =
    it("As a claimant, I should be able to submit a claim application through the portal", () => {
      portal.before();
      //@TODO adjust the generate claim for multiple different types and leave periods
      // Go to cypress.ts and adjust the CPS_SP by uncomment lines for what is needed to be tested.
      cy.task("generateClaim", "CPS_SP").then((claim) => {
        cy.stash("claim", claim);
        const application: ApplicationRequestBody = claim.claim;
        const paymentPreference = claim.paymentPreference;

        const credentials: Credentials = {
          username: config("PORTAL_USERNAME"),
          password: config("PORTAL_PASSWORD"),
        };
        cy.stash("credentials", credentials);
        portal.login(credentials);
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
        portal.submitPartsTwoThreeNoLeaveCert(paymentPreference);
      });
    });

  //Fineos check absence case here.
  it(
    "Should check the claim in Fineos.",
    { baseUrl: getFineosBaseUrl() },
    () => {
      cy.dependsOnPreviousPass([submissionTest]);
      fineos.before();
      cy.visit("/");
      cy.unstash<DehydratedClaim>("claim").then((claim) => {
        cy.unstash<Submission>("submission").then((submission) => {
          const claimPage = fineosPages.ClaimPage.visit(
            submission.fineos_absence_id
          );
          claimPage.adjudicate((adjudicate) => {
            adjudicate.evidence((evidence) => {
              claim.documents.forEach((document) => {
                evidence.receive(document.document_type);
              });
            });
            adjudicate.certificationPeriods((cert) => cert.prefill());
            adjudicate.acceptLeavePlan();
          });
          claimPage.shouldHaveStatus("Applicability", "Applicable");
          claimPage.shouldHaveStatus("Eligibility", "Met");
          claimPage.shouldHaveStatus("Evidence", "Satisfied");
          // If continuous leave or reduced leave use this availability.
          claimPage.shouldHaveStatus("Availability", "Time Available");
          // If intermittent leave use this Availability.
          // claimPage.shouldHaveStatus("Availability", "As Certified");
          claimPage.shouldHaveStatus("Restriction", "Passed");
          claimPage.shouldHaveStatus("PlanDecision", "Accepted");
          claimPage.outstandingRequirements((outstandingRequirements) => {
            outstandingRequirements.complete();
          });
          claimPage.approve();
        });
      });
    }
  );
});
