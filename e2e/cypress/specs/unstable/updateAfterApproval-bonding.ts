import { fineos, portal, email, fineosPages } from "../../actions";
import { getFineosBaseUrl } from "../../config";
import { Submission } from "../../../src/types";
import { extractLeavePeriod } from "../../../src/util/claims";
import {
  findCertificationDoc,
  getDocumentReviewTaskName,
} from "../../../src/util/documents";

describe("Post-approval (notifications/notices)", { retries: 0 }, () => {
  after(() => {
    portal.deleteDownloadsFolder();
  });
  const credentials: Credentials = {
    username: Cypress.env("E2E_PORTAL_USERNAME"),
    password: Cypress.env("E2E_PORTAL_PASSWORD"),
  };

  const submit = it(
    "Given a fully approved claim",
    { baseUrl: getFineosBaseUrl() },
    () => {
      fineos.before();
      cy.visit("/");
      // Submit a claim via the API, including Employer Response.
      cy.task("generateClaim", "BHAP1ER").then((claim) => {
        cy.stash("claim", claim.claim);
        cy.task("submitClaimToAPI", {
          ...claim,
          credentials,
        }).then((response) => {
          if (!response.fineos_absence_id) {
            throw new Error("Response contained no fineos_absence_id property");
          }

          const [, endDate] = extractLeavePeriod(claim.claim);
          cy.stash("submission", {
            application_id: response.application_id,
            fineos_absence_id: response.fineos_absence_id,
            timestamp_from: Date.now(),
          });

          const claimPage = fineosPages.ClaimPage.visit(
            response.fineos_absence_id
          );
          claimPage.adjudicate((adjudication) => {
            adjudication.evidence((evidence) => {
              // Receive and approve all of the documentation for the claim.
              claim.documents.forEach((doc) =>
                evidence.receive(doc.document_type)
              );
            });
            adjudication.certificationPeriods((cert) => cert.prefill());
            adjudication.acceptLeavePlan();
          });
          claimPage.tasks((tasks) => {
            const certificationDoc = findCertificationDoc(claim.documents);
            const certificationTask = getDocumentReviewTaskName(
              certificationDoc.document_type
            );
            tasks.assertTaskExists("ID Review");
            tasks.assertTaskExists(certificationTask);
          });
          claimPage.shouldHaveStatus("Applicability", "Applicable");
          claimPage.shouldHaveStatus("Eligibility", "Met");
          claimPage.shouldHaveStatus("Evidence", "Satisfied");
          claimPage.shouldHaveStatus("Availability", "Time Available");
          claimPage.shouldHaveStatus("Restriction", "Passed");
          claimPage.shouldHaveStatus("PlanDecision", "Accepted");
          claimPage.approve();
          claimPage.triggerNotice("Approval Notice");
          fineos.claimAddTimeAfterApproval(response.fineos_absence_id, endDate);
        });
      });
    }
  );

  it(
    "Should receive am Employer Response 'Action Required' notification",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass([submit]);
      cy.unstash<Submission>("submission").then((submission) => {
        cy.unstash<ApplicationRequestBody>("claim").then((claim) => {
          email
            .getEmails(
              {
                address: "gqzap.notifications@inbox.testmail.app",
                subject: `Action required: Respond to ${claim.first_name} ${claim.last_name}'s paid leave application`,
                messageWildcard: submission.fineos_absence_id,
                timestamp_from: submission.timestamp_from,
                debugInfo: { "Fineos Claim ID": submission.fineos_absence_id },
              },
              180000
            )
            .then((emails) => {
              expect(emails[0].html).to.contain(
                `/employers/applications/new-application/?absence_id=${submission.fineos_absence_id}`
              );
            });
        });
      });
    }
  );
});
