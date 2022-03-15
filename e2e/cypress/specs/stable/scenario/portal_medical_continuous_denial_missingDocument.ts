import { fineos, fineosPages, portal } from "../../../actions";
import { Submission, ValidConcurrentLeave } from "../../../../src/types";
import { format, parseISO } from "date-fns";
import { assertValidClaim } from "../../../../src/util/typeUtils";

// Used for stash generated concurrent leave dates
type ConcurrentLeave = {
  concurrentLeave: ValidConcurrentLeave;
};

describe("Submit a bonding claim and adjucation approval - BHAP1", () => {
  const submissionTest =
    it("As a claimant, I should be able to submit a continous bonding application through the portal", () => {
      portal.before();
      cy.task("generateClaim", "CONCURRENT").then((claim) => {
        cy.stash("claim", claim);
        const application: ApplicationRequestBody = claim.claim;
        const paymentPreference = claim.paymentPreference;
        const concurrentLeave = claim.claim.concurrent_leave;
        cy.stash("ConcurrentLeave", {
          concurrentLeave,
        });

        portal.loginClaimant();
        portal.skipLoadingClaimantApplications();

        // Submit Claim
        portal.startClaim();
        portal.submitClaimPartOne(application, false);
        portal.waitForClaimSubmission().then((data) => {
          cy.stash("submission", {
            application_id: data.application_id,
            fineos_absence_id: data.fineos_absence_id,
            timestamp_from: Date.now(),
          });
        });
        portal.submitPartsTwoThreeNoLeaveCert(
          paymentPreference,
          claim.is_withholding_tax
        );
      });
    });

  const adjudicate =
    it("Should check hours worked per week/upload state managed document/mark evidence received", () => {
      cy.dependsOnPreviousPass([submissionTest]);
      fineos.before();

      cy.unstash<DehydratedClaim>("claim").then((claim) => {
        cy.unstash<Submission>("submission").then((submission) => {
          assertValidClaim(claim.claim);
          const reason = claim.claim.leave_details.reason;
          if (!reason) throw new Error(`No claim type given`);
          fineosPages.ClaimPage.visit(submission.fineos_absence_id)
            .documents((docs) => {
              docs
                .assertDocumentExists("Identification Proof")
                // Upload the form missing in initial application
                .uploadDocument("Own serious health condition form");
            })
            .adjudicate((adjudication) => {
              adjudication
                .requestInformation((reqInfo) => {
                  if (claim.claim.hours_worked_per_week)
                    reqInfo.assertHoursWorkedPerWeek(
                      claim.claim.hours_worked_per_week
                    );
                })
                .evidence((evidence) => {
                  claim.documents.forEach((doc) =>
                    evidence.receive(doc.document_type)
                  );
                  // Mark missing doc as recieved
                  evidence.receive("Own serious health condition form");
                });
            });
        });
      });
    });

  // Check Application card in portal for document uploaded in Fineos
  it("I should be able to see that a document has been uploaded in the portal", () => {
    cy.dependsOnPreviousPass([submissionTest, adjudicate]);
    portal.before();

    portal.loginClaimant();
    portal.skipLoadingClaimantApplications();
    cy.unstash<Submission>("submission").then((submission) => {
      portal.goToUploadCertificationPage(submission.application_id);
      cy.contains("form", "Upload your certification form")
        .find("*[data-test='file-card']", { timeout: 30000 })
        .should("have.length", 1);
    });
  });

  it("Should check for hours worked per week & report conflict on Employer Response Form and check concurrent leave dates", () => {
    cy.dependsOnPreviousPass();
    portal.before();
    cy.unstash<DehydratedClaim>("claim").then((claim) => {
      cy.unstash<Submission>("submission").then((submission) => {
        cy.unstash<ConcurrentLeave>("ConcurrentLeave").then(
          ({ concurrentLeave }) => {
            assertValidClaim(claim.claim);
            portal.loginLeaveAdmin(claim.claim.employer_fein);
            portal.visitActionRequiredERFormPage(submission.fineos_absence_id);
            portal.checkHoursPerWeekLeaveAdmin(
              claim.claim.hours_worked_per_week as number
            );
            const newStart = format(
              parseISO(concurrentLeave.leave_start_date),
              "M/d/yyyy"
            );
            const newEnd = format(
              parseISO(concurrentLeave.leave_end_date),
              "M/d/yyyy"
            );
            portal.checkConcurrentLeave(newStart, newEnd);
            portal.respondToLeaveAdminRequest(false, false, false);
          }
        );
      });
    });
  });
});
