import { fineos, portal, email, fineosPages } from "../../../actions";
import { Submission } from "../../../../src/types";
import { findCertificationDoc } from "../../../../src/util/documents";
import { getClaimantCredentials } from "../../../config";
import { format, addDays } from "date-fns";
import { extractLeavePeriod } from "../../../../src/util/claims";
import { DehydratedClaim } from "generation/Claim";

describe("Request for More Information (notifications/notices)", () => {
  after(() => {
    portal.deleteDownloadsFolder();
  });
  const submission = it("Generates and submits a caring leave claim", () => {
    cy.task("generateClaim", "CHAP_RFI").then((claim) => {
      cy.task("submitClaimToAPI", claim).then((res) => {
        cy.stash("claim", claim);
        cy.stash("submission", {
          application_id: res.application_id,
          fineos_absence_id: res.fineos_absence_id,
          timestamp_from: Date.now(),
        });
      });
    });
  });
  const modification = it("CSR rep can modify leave dates pre-approval", () => {
    cy.dependsOnPreviousPass([submission]);
    fineos.before();
    cy.unstash<DehydratedClaim>("claim").then((claim) => {
      cy.unstash<Submission>("submission").then((submission) => {
        const [startDate, endDate] = extractLeavePeriod(claim.claim);
        const newStartDate = format(
          addDays(new Date(startDate), 1),
          "MM/dd/yyyy"
        );
        const newEndDate = format(addDays(new Date(endDate), 1), "MM/dd/yyyy");
        cy.stash("modifiedLeaveDates", [newStartDate, newEndDate]);
        fineosPages.ClaimPage.visit(submission.fineos_absence_id)
          .adjudicate((adjudication) => {
            adjudication.requestInformation((requestInformation) => {
              requestInformation.editRequestDates(newStartDate, newEndDate);
            });
          })
          .triggerNotice("Preliminary Designation");
      });
    });
  });
  const requestForInformation =
    it("CSR rep can trigger a request for additional information", () => {
      cy.dependsOnPreviousPass([modification]);
      fineos.before();
      cy.unstash<DehydratedClaim>("claim").then((claim) => {
        cy.unstash<Submission>("submission").then((submission) => {
          fineosPages.ClaimPage.visit(submission.fineos_absence_id)
            .adjudicate((adjudicate) => {
              adjudicate
                .evidence((evidence) => {
                  const certificationDocument = findCertificationDoc(
                    claim.documents
                  );
                  evidence.requestAdditionalInformation(
                    certificationDocument.document_type,
                    {
                      "Care Information incomplete": "This is incomplete",
                    },
                    "Please resubmit page 1 of the Caring Certification form to verify the claimant's demographic information.  The page provided is missing information.  Thank you."
                  );
                })
                .certificationPeriods((certificationPeriods) =>
                  certificationPeriods.prefill()
                );
            })
            .tasks((task) => {
              task.assertTaskExists("Caring Certification Review");
              task.close("Caring Certification Review");
            })
            .documents((document) => {
              document.assertDocumentUploads(
                "Care for a family member form",
                1
              );
            })
            .shouldHaveStatus("PlanDecision", "Undecided")
            .triggerNotice("SOM Generate Legal Notice")
            .documents((docPage) =>
              docPage.assertDocumentExists("Request for more Information")
            );
        });
      });
    });
  const upload =
    it("Should allow claimant to upload additional documents and generate a legal notice (Request for Information) that the claimant can view", () => {
      cy.dependsOnPreviousPass([modification]);
      portal.before();
      cy.unstash<Submission>("submission").then((submission) => {
        portal.loginClaimant();
        cy.log("Waiting for documents");
        cy.task(
          "waitForClaimDocuments",
          {
            credentials: getClaimantCredentials(),
            application_id: submission.application_id,
            document_type: "Request for more Information",
          },
          { timeout: 60000 }
        );
        cy.log("Finished waiting for documents");
        cy.unstash<[string, string]>("modifiedLeaveDates").then(
          ([start, end]) => {
            portal.claimantGoToClaimStatus(submission.fineos_absence_id);
            portal.claimantAssertClaimStatus([
              {
                leave: "Care for a Family Member",
                status: "Pending",
                leavePeriods: [
                  format(new Date(start), "MMMM d, yyyy"),
                  format(new Date(end), "MMMM d, yyyy"),
                ],
              },
            ]);
            cy.findByText("Request for more information (PDF)")
              .should("be.visible")
              .click({ force: true });
            portal.downloadLegalNotice(submission.fineos_absence_id);
          }
        );
        portal.uploadAdditionalDocument("Certification", "caring");
      });
    });
  it("CSR rep can view the additional information uploaded by claimant", () => {
    cy.dependsOnPreviousPass([upload]);
    fineos.before();
    cy.unstash<Submission>("submission").then((submission) => {
      const page = fineosPages.ClaimPage.visit(submission.fineos_absence_id);
      page.tasks((taskPage) =>
        taskPage.assertTaskExists("Caring Certification Review")
      );
      page.documents((documentsPage) => {
        documentsPage.assertDocumentUploads("Care for a family member form", 2);
      });
    });
  });
  it(
    "I should receive a 'Thank you for successfully submitting your ... application' notification (employee)",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass([submission]);
      cy.unstash<Submission>("submission").then((submission) => {
        email.getEmails(
          {
            address: "gqzap.notifications@inbox.testmail.app",
            subject:
              "Thank you for successfully submitting your Paid Family and Medical Leave Application",
            timestamp_from: submission.timestamp_from,
            messageWildcard: submission.fineos_absence_id,
            debugInfo: { "Fineos Claim ID": submission.fineos_absence_id },
          },
          30000
        );
        cy.contains(submission.fineos_absence_id);
      });
    }
  );
  it(
    "Should generate a (Request for Information) notification for the claimant",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass([requestForInformation]);
      cy.unstash<Submission>("submission").then((submission) => {
        const subjectClaimant = email.getNotificationSubject(
          "request for additional info",
          submission.fineos_absence_id
        );
        cy.log(subjectClaimant);
        email.getEmails(
          {
            address: "gqzap.notifications@inbox.testmail.app",
            subjectWildcard: subjectClaimant,
            messageWildcard: submission.fineos_absence_id,
            timestamp_from: submission.timestamp_from,
            debugInfo: {
              "Fineos Claim ID": submission.fineos_absence_id,
            },
          },
          40000
        );
        cy.contains(submission.fineos_absence_id);
      });
    }
  );
});
