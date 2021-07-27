import { fineos, email, fineosPages } from "../../actions";
import { getFineosBaseUrl } from "../../config";
import { Submission } from "../../../src/types";
import { ApplicationRequestBody } from "../../../src/api";
import { assertValidClaim } from "../../../src/util/typeUtils";

describe("Create a new continuous leave, bonding claim in FINEOS", () => {
  const submit = it(
    "Should be able to create a claim",
    { baseUrl: getFineosBaseUrl() },
    () => {
      fineos.before();

      cy.visit("/");
      cy.task("generateClaim", "BHAP1").then((claim) => {
        assertValidClaim(claim.claim);
        cy.stash("claim", claim.claim);
        fineosPages.ClaimantPage.visit(claim.claim.tax_identifier)
          .createNotification(claim.claim)
          .then((fineos_absence_id) => {
            cy.log(fineos_absence_id);
            cy.stash("submission", {
              fineos_absence_id: fineos_absence_id,
              timestamp_from: Date.now(),
            });
          });
      });
    }
  );

  it(
    "I should receive an 'application started' notification",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass([submit]);
      cy.unstash<ApplicationRequestBody>("claim").then((claim) => {
        cy.unstash<Submission>("submission").then((submission) => {
          const employeeFullName = `${claim.first_name} ${claim.last_name}`;
          cy.log(employeeFullName);
          const subject = email.getNotificationSubject(
            employeeFullName,
            "application started",
            submission.fineos_absence_id
          );
          email
            .getEmails(
              {
                address: "gqzap.notifications@inbox.testmail.app",
                subject: subject,
                messageWildcard: submission.fineos_absence_id,
                timestamp_from: submission.timestamp_from,
                debugInfo: { "Fineos Claim ID": submission.fineos_absence_id },
              },
              180000
            )
            .then(() => {
              cy.contains(employeeFullName);
              cy.contains(submission.fineos_absence_id);
            });
        });
      });
    }
  );
});
