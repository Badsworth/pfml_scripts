import { fineos, portal, fineosPages } from "../../../actions";
import { Submission } from "../../../../src/types";
import {
  findCertificationDoc,
  getDocumentReviewTaskName,
} from "../../../../src/util/documents";

describe("Approval (notifications/notices)", () => {
  after(() => {
    portal.deleteDownloadsFolder();
  });

  it("Given a fully approved claim", () => {
    fineos.before();
    cy.visit("/");
    // Submit a claim via the API, including Employer Response.
    cy.task("generateClaim", "REDUCED_ER").then((claim) => {
      cy.task("submitClaimToAPI", claim).then((response) => {
        if (!response.fineos_absence_id) {
          throw new Error("Response contained no fineos_absence_id property");
        }
        cy.stash("submission", {
          application_id: response.application_id,
          fineos_absence_id: response.fineos_absence_id,
          timestamp_from: Date.now(),
        });
        fineosPages.ClaimPage.visit(response.fineos_absence_id)
          .adjudicate((adjudication) => {
            adjudication
              .evidence((evidence) => {
                // Receive and approve all of the documentation for the claim.
                claim.documents.forEach((doc) =>
                  evidence.receive(doc.document_type)
                );
              })
              .certificationPeriods((cert) => cert.prefill())
              .acceptLeavePlan();
          })
          .tasks((tasks) => {
            const certificationDoc = findCertificationDoc(claim.documents);
            const certificationTask = getDocumentReviewTaskName(
              certificationDoc.document_type
            );
            tasks.assertTaskExists("ID Review");
            tasks.assertTaskExists(certificationTask);
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
  });

  it("Records Cancellation", () => {
    cy.dependsOnPreviousPass();
    fineos.before();
    cy.visit("/");
    cy.unstash<Submission>("submission").then(({ fineos_absence_id }) => {
      fineosPages.ClaimPage.visit(fineos_absence_id)
        .recordCancellation()
        .tasks((tasks) => {
          tasks
            .all()
            .assertTaskExists("Review and Decision Cancel Time Submitted");
        })
        .documents((docsPage) => {
          docsPage.assertDocumentExists("Record Cancel Time");
        });
    });
  });
});
