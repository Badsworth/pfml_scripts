import { fineos, fineosPages, portal } from "../../actions";
import { getLeaveAdminCredentials } from "../../config";
import { Submission } from "../../../src/types";
import { config } from "../../actions/common";
import { assertValidClaim } from "../../../src/util/typeUtils";

describe("Submit bonding application via the web portal: Adjudication Approval & payment checking", () => {
  const submissionTest =
    it("As a claimant, I should be able to submit a continous bonding application through the portal", () => {
      portal.before();
      cy.task("generateClaim", "BCAP90").then((claim) => {
        cy.stash("claim", claim);
        const application: ApplicationRequestBody = claim.claim;
        const paymentPreference = claim.paymentPreference;

        const credentials: Credentials = {
          username: config("PORTAL_USERNAME"),
          password: config("PORTAL_PASSWORD"),
        };
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
        portal.submitClaimPartsTwoThree(application, paymentPreference);
      });
    });

  it("Leave admin will submit ER approval for employee", () => {
    cy.dependsOnPreviousPass([submissionTest]);
    portal.before();
    cy.unstash<DehydratedClaim>("claim").then((claim) => {
      cy.unstash<Submission>("submission").then((submission) => {
        assertValidClaim(claim.claim);
        portal.login(getLeaveAdminCredentials(claim.claim.employer_fein));
        portal.selectClaimFromEmployerDashboard(submission.fineos_absence_id);
        portal.visitActionRequiredERFormPage(submission.fineos_absence_id);
        portal.respondToLeaveAdminRequest(false, true, true);
      });
    });
  });

  it(
    "CSR rep will approve continuous bonding application",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass();
      fineos.before();
      cy.unstash<DehydratedClaim>("claim").then((claim) => {
        cy.unstash<Submission>("submission").then((submission) => {
          const claimPage = fineosPages.ClaimPage.visit(
            submission.fineos_absence_id
          );
          claimPage.adjudicate((adjudication) => {
            adjudication.evidence((evidence) => {
              // Receive all of the claim documentation.
              claim.documents.forEach((document) => {
                evidence.receive(document.document_type);
              });
            });
            adjudication.certificationPeriods((cert) => cert.prefill());
            adjudication.acceptLeavePlan();
          });
          claimPage.shouldHaveStatus("Applicability", "Applicable");
          claimPage.shouldHaveStatus("Eligibility", "Met");
          claimPage.shouldHaveStatus("Evidence", "Satisfied");
          claimPage.shouldHaveStatus("Availability", "Time Available");
          claimPage.shouldHaveStatus("Restriction", "Passed");
          claimPage.shouldHaveStatus("PlanDecision", "Accepted");
          claimPage.approve();
        });
      });
    }
  );

  it("Should be able to confirm the weekly payment amount", () => {
    cy.dependsOnPreviousPass();
    fineos.before();

    cy.unstash<DehydratedClaim>("claim").then((claim) => {
      cy.unstash<Submission>("submission").then((submission) => {
        const page = fineosPages.ClaimPage.visit(submission.fineos_absence_id);
        page.paidLeave((paidLeavePage) => {
          if (claim.claim.mailing_address)
            paidLeavePage.assertPaymentAddress(claim.claim.mailing_address);
          if (claim.paymentPreference)
            paidLeavePage.assertPaymentPreference(claim.paymentPreference);
          paidLeavePage.assertAmountsPending([
            {
              net_payment_amount: parseInt(
                claim.metadata?.expected_weekly_payment as string
              ),
            },
          ]);
        });
      });
    });
  });
});
