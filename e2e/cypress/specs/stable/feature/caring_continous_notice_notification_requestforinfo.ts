import { fineos, portal, email, fineosPages } from "../../../actions";
import { getFineosBaseUrl } from "../../../config";
import { Submission } from "../../../../src/types";
import { config } from "../../../actions/common";
import { findCertificationDoc } from "../../../../src/util/documents";

describe("Request for More Information (notifications/notices)", () => {
  after(() => {
    portal.deleteDownloadsFolder();
  });

  const credentials: Credentials = {
    username: config("PORTAL_USERNAME"),
    password: config("PORTAL_PASSWORD"),
  };

  const submit = it(
    "Given a claim in which a CSR has requested more information",
    { baseUrl: getFineosBaseUrl() },
    () => {
      fineos.before();
      cy.visit("/");

      cy.task("generateClaim", "CHAP_RFI").then((claim) => {
        cy.task("submitClaimToAPI", {
          ...claim,
          credentials,
        }).then((res) => {
          cy.stash("claim", claim.claim);
          cy.stash("submission", {
            application_id: res.application_id,
            fineos_absence_id: res.fineos_absence_id,
            timestamp_from: Date.now(),
          });

          const page = fineosPages.ClaimPage.visit(res.fineos_absence_id);
          page.adjudicate((adjudication) => {
            adjudication.evidence((evidence) => {
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
            });
          });
          page.tasks((task) => {
            task.assertTaskExists("Caring Certification Review");
            task.close("Caring Certification Review");
          });
          page.documents((document) => {
            document.assertDocumentUploads("Care for a family member form", 1);
          });
          // This should trigger a change in plan status.
          page.shouldHaveStatus("PlanDecision", "Pending Evidence");
          page
            .triggerNotice("SOM Generate Legal Notice")
            .documents((docPage) =>
              docPage.assertDocumentExists("Request for more Information")
            );
        });
      });
    }
  );

  const upload = it(
    "Should allow claimant to upload additional documents and generate a legal notice (Request for Information) that the claimant can view",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass([submit]);
      portal.before();
      cy.unstash<Submission>("submission").then((submission) => {
        portal.login(credentials);
        cy.log("Waiting for documents");
        cy.task(
          "waitForClaimDocuments",
          {
            credentials: credentials,
            application_id: submission.application_id,
            document_type: "Request for more Information",
          },
          { timeout: 60000 }
        );
        cy.log("Finished waiting for documents");
        cy.visit("/applications");
        cy.contains("article", submission.fineos_absence_id).within(() => {
          cy.findByText("Request for more information (PDF)")
            .should("be.visible")
            .click();
        });
        portal.downloadLegalNotice(submission.fineos_absence_id);
        portal.uploadAdditionalDocument(
          submission.fineos_absence_id,
          "Certification",
          "caring"
        );
      });
    }
  );

  it(
    "CSR rep can view the additional information uploaded by claimant",
    { baseUrl: getFineosBaseUrl() },
    () => {
      cy.dependsOnPreviousPass([submit, upload]);
      fineos.before();
      cy.visit("/");
      cy.unstash<Submission>("submission").then((submission) => {
        const page = fineosPages.ClaimPage.visit(submission.fineos_absence_id);
        page.tasks((taskPage) =>
          taskPage.assertTaskExists("Caring Certification Review")
        );
        page.documents((documentsPage) => {
          documentsPage.assertDocumentUploads(
            "Care for a family member form",
            2
          );
        });
      });
    }
  );

  it(
    "I should receive a 'Thank you for successfully submitting your ... application' notification (employee)",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass([submit]);
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
      cy.dependsOnPreviousPass([submit]);
      cy.unstash<Submission>("submission").then((submission) => {
        cy.unstash<ApplicationRequestBody>("claim").then((claim) => {
          const employeeFullName = `${claim.first_name} ${claim.last_name}`;
          const subjectClaimant = email.getNotificationSubject(
            employeeFullName,
            "request for additional info",
            submission.fineos_absence_id
          );
          cy.log(subjectClaimant);
          email.getEmails(
            {
              address: "gqzap.notifications@inbox.testmail.app",
              subject: subjectClaimant,
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
      });
    }
  );
});
