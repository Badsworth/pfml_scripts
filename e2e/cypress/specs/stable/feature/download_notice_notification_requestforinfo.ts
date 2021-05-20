import { fineos, portal, email } from "../../../actions";
import { getFineosBaseUrl } from "../../../config";
import { Submission } from "../../../../src/types";
import { config } from "../../../actions/common";

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

      cy.task("generateClaim", "BHAP1").then((claim) => {
        cy.task("submitClaimToAPI", {
          ...claim,
          credentials,
        }).then((responseData: ApplicationResponse) => {
          if (!responseData.fineos_absence_id) {
            throw new Error("FINEOS ID must be specified");
          }
          cy.stash("claim", claim.claim);
          cy.stash("submission", {
            application_id: responseData.application_id,
            fineos_absence_id: responseData.fineos_absence_id,
            timestamp_from: Date.now(),
          });
          fineos.visitClaim(responseData.fineos_absence_id);
          fineos.assertClaimStatus("Adjudication");
          fineos.additionalEvidenceRequest(responseData.fineos_absence_id);
          fineos.triggerNoticeRelease("Request for more Information");
        });
      });
    }
  );

  it(
    "Should generate a legal notice (Request for Information) that the claimant can view",
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
          { timeout: 300000 }
        );
        cy.log("Finished waiting for documents");
        cy.visit("/applications");
        cy.contains("article", submission.fineos_absence_id).within(() => {
          cy.contains("a", "Request for more information")
            .should("be.visible")
            .click();
        });
        portal.downloadLegalNotice("Request", submission.fineos_absence_id, 3);
      });
    }
  );

  it(
    "I should receive a 'Thank you for successfully submitting your ... application' notification (employee)",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass([submit]);
      cy.unstash<Submission>("submission").then((submission) => {
        email
          .getEmails(
            {
              address: "gqzap.notifications@inbox.testmail.app",
              subject:
                "Thank you for successfully submitting your Paid Family and Medical Leave Application",
              timestamp_from: submission.timestamp_from,
              messageWildcard: submission.fineos_absence_id,
              debugInfo: { "Fineos Claim ID": submission.fineos_absence_id },
            },
            180000
          )
          .should("not.be.empty");
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
          email
            .getEmails(
              {
                address: "gqzap.notifications@inbox.testmail.app",
                subject: subjectClaimant,
                messageWildcard: submission.fineos_absence_id,
                timestamp_from: submission.timestamp_from,
                debugInfo: { "Fineos Claim ID": submission.fineos_absence_id },
              },
              60000
            )
            .should("not.be.empty");
        });
      });
    }
  );
});
