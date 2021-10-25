import { fineos, fineosPages, portal } from "../../actions";
import {getClaimantCredentials, getFineosBaseUrl} from "../../config";
import { Submission } from "../../../src/types";
import { addMonths, addDays, format } from "date-fns";

describe("Submit medical pre-birth application via the web portal", () => {
  const submission =
    it("Submits a Medical/Pregnancy claim through the API", () => {
      cy.task("generateClaim", "PREBIRTH").then((claim) => {
        cy.task("submitClaimToAPI", claim).then((submission) => {
          cy.stash("claim", claim);
          cy.stash("submission", {
            application_id: submission.application_id,
            fineos_absence_id: submission.fineos_absence_id,
            timestamp_from: Date.now(),
          });
        });
      });
    });
  it(
    "CSR rep will approve reduced medical application",
    { retries: 0, baseUrl: getFineosBaseUrl() },
    () => {
      cy.dependsOnPreviousPass([submission]);
      fineos.before();
      cy.visit("/");
      cy.unstash<DehydratedClaim>("claim").then((claim) => {
        cy.unstash<Submission>("submission").then((submission) => {
          fineosPages.ClaimPage.visit(submission.fineos_absence_id)
            .adjudicate((adjudication) => {
              adjudication
                .evidence((evidence) => {
                  // Receive all of the claim documentation.
                  claim.documents.forEach((document) => {
                    evidence.receive(document.document_type);
                  });
                })
                .certificationPeriods((cert) => cert.prefill())
                .acceptLeavePlan();
            })
            .shouldHaveStatus("Applicability", "Applicable")
            .shouldHaveStatus("Eligibility", "Met")
            .shouldHaveStatus("Evidence", "Satisfied")
            .shouldHaveStatus("Availability", "Time Available")
            .shouldHaveStatus("Restriction", "Passed")
            .shouldHaveStatus("PlanDecision", "Accepted")
            .approve();
        });
      });
    }
  );
  it(
    "CSR rep will add a bonding leave to the absence case",
    { retries: 0, baseUrl: getFineosBaseUrl() },
    () => {
      cy.dependsOnPreviousPass([submission]);
      fineos.before();
      // wait 30s before modifying approved absence case, there's a good chance we'll see a fatal fineos error page without waiting here
      cy.wait(1000 * 30);
      cy.unstash<Submission>("submission").then((submission) => {
        fineosPages.ClaimPage.visit(submission.fineos_absence_id)
          .benefitsExtension((benefitsExtension) => {
            const startDate = addMonths(new Date(), 2);
            const startDateFormatted = format(startDate, "MM/dd/yyyy");
            const endDateFormatted = format(
              addDays(startDate, 2),
              "MM/dd/yyyy"
            );
            benefitsExtension.extendLeave(
              startDateFormatted,
              endDateFormatted,
              true,
              "reduced"
            );
          })
      });
    }
  );
  const upload =
    it("Should allow claimant to upload proof of birth and generate a legal notice that the claimant can view", () => {
      cy.dependsOnPreviousPass([submission]);
      portal.before();
      portal.loginClaimant();
      cy.unstash<Submission>("submission").then((submission) => {
            portal.claimantGoToClaimStatus(submission.fineos_absence_id);
            portal.claimantAssertClaimStatus([
              {
                leave: "Serious Health Condition - Employee",
                status: "Approved",
              },
            ]);
          }
        );
        portal.uploadAdditionalDocument("Proof of birth", "birth-certificate");
    });
  it("CSR rep can view the Child Bonding evidence form uploaded by claimant", () => {
    cy.dependsOnPreviousPass([upload]);
    fineos.before();
    cy.unstash<Submission>("submission").then((submission) => {
      const page = fineosPages.ClaimPage.visit(submission.fineos_absence_id);
      page.tasks((taskPage) =>
        taskPage.assertTaskExists("Bonding Certification Review")
      );
      page.documents((documentsPage) => {
        documentsPage.assertDocumentUploads("Child bonding evidence form");
      });
    });
  });
});
