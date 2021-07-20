import { fineos, email } from "../../actions";
import { extractLeavePeriod } from "../../../src/util/claims";
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
        fineos.searchClaimantSSN(claim.claim.tax_identifier);
        fineos.clickBottomWidgetButton("OK");
        fineos.assertOnClaimantPage(
          claim.claim.first_name,
          claim.claim.last_name
        );
        const [startDate, endDate] = extractLeavePeriod(claim.claim);
        fineos.createNotification(startDate, endDate, "bonding", claim.claim);
        cy.get("a[name*='CaseMapWidget']")
          .invoke("text")
          .then((text) => {
            const fineos_absence_id = text.slice(24);
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
