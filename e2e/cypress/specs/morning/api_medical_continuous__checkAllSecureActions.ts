import { fineos, fineosPages } from "../../actions";
import { Submission } from "../../../src/types";
import { waitForAjaxComplete } from "../../actions/fineos";
import { assertValidClaim } from "../../../src/util/typeUtils";
import { config } from "../../actions/common";

// We are using the following MHAP1_OLB_ER scenario to create a claim to use with
// "api_bonding_reduced_approval_fullOffsetRecoveryOverpayment.ts" if needed for CPS testing.
describe("Create a new caring leave claim in FINEOS and check multiple secure actions", () => {
  const adjClaim = it("Create an absence case through the API", () => {
    cy.task("generateClaim", "MHAP1_OLB_ER").then((claim) => {
      cy.task("submitClaimToAPI", claim).then((res) => {
        cy.stash("claim", claim);
        assertValidClaim(claim.claim);
        cy.stash("submission", {
          application_id: res.application_id,
          fineos_absence_id: res.fineos_absence_id,
          timestamp_from: Date.now(),
        });
      });
    });
  });

  it(
    "Check to see if can create a Historical Absence case (secure action) within an Absence Case",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass([adjClaim]);
      fineos.before();
      cy.unstash<Submission>("submission").then((submission) => {
        fineosPages.ClaimPage.visit(
          submission.fineos_absence_id
        ).addHistoricalAbsenceCase();
      });
    }
  );

  it(
    "Check to see if the Suppress Correspondence (secure action) is available in the Absence Case",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass([adjClaim]);
      fineos.before();
      cy.unstash<Submission>("submission").then((submission) => {
        fineosPages.ClaimPage.visit(submission.fineos_absence_id)
          .removeSuppressCorrespondence()
          .documents((docsPage) => {
            docsPage.assertDocumentExists("Notification Suppression Disabled");
          });
      });
    }
  );

  const approveClaim =
    it("Approve the Absence Case for the other secure actions checks", () => {
      cy.dependsOnPreviousPass([adjClaim]);
      fineos.before();
      cy.unstash<Submission>("submission").then((submission) => {
        const claimPage = fineosPages.ClaimPage.visit(
          submission.fineos_absence_id
        );
        claimPage.adjudicate((adjudicate) => {
          adjudicate.evidence((evidence) => {
            evidence.receive("Own serious health condition form");
            evidence.receive("Identification Proof");
          });
          adjudicate.certificationPeriods((cert) => cert.prefill());
          adjudicate.acceptLeavePlan();
        });
        claimPage.approve("Approved", config("HAS_APRIL_UPGRADE") === "true");
      });
    });

  it(
    "Check to see if certain users are able to change or edit the document type (secure action)",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass([adjClaim, approveClaim]);
      fineos.before();
      cy.unstash<Submission>("submission").then((submission) => {
        fineosPages.ClaimPage.visit(submission.fineos_absence_id).documents(
          (docPage) => {
            docPage.changeDocType(
              "Identification Proof",
              "State managed Paid Leave Confirmation",
              true
            );
          }
        );
      });
    }
  );

  it(
    "Check to see if the O/R buttons are enabled for the following buttons: Complete, Suppress, & Remove (secure action)",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass([adjClaim, approveClaim]);
      fineos.before();
      cy.unstash<Submission>("submission").then((submission) => {
        const claimPage = fineosPages.ClaimPage.visit(
          submission.fineos_absence_id
        );
        claimPage.outstandingRequirements((outstanding_requirement) => {
          outstanding_requirement.add();
          waitForAjaxComplete();
          outstanding_requirement.complete(
            "Received",
            "Complete Employer Confirmation",
            true
          );
          waitForAjaxComplete();
          outstanding_requirement.reopen(true);
          waitForAjaxComplete();
          outstanding_requirement.suppress(
            "Auto-Suppressed",
            "Suppress Employer Confirmation",
            true
          );
          waitForAjaxComplete();
          outstanding_requirement.reopen(true);
          waitForAjaxComplete();
          outstanding_requirement.removeOR(true);
        });
      });
    }
  );

  it(
    "Check the Claimant profile to see if bulk payee is enabled under Payment Preferences (secure action)",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass([adjClaim, approveClaim]);
      fineos.before();
      cy.unstash<DehydratedClaim>("claim").then((claim) => {
        assertValidClaim(claim.claim);
        fineosPages.ClaimantPage.visit(claim.claim.tax_identifier)
          .paymentPreferences()
          .edit()
          .checkBulkPayee(true);
      });
    }
  );
});
