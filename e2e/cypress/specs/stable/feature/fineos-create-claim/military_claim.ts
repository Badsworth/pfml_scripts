import { fineos, email } from "../../../../tests/common/actions";
import {
  bailIfThisTestFails,
  beforeFineos,
} from "../../../../tests/common/before";
import { extractLeavePeriod } from "../../../../utils";
import { getFineosBaseUrl } from "../../../../config";
import { Submission } from "../../../../../src/types";

describe("Create a new continuous leave, military caregiver claim in FINEOS", () => {
  it(
    "Should be able to create a claim",
    { baseUrl: getFineosBaseUrl() },
    () => {
      beforeFineos();
      bailIfThisTestFails();

      cy.visit("/");
      cy.task("generateClaim", "BHAP1").then((claim) => {
        cy.stash("claim", claim.claim);
        if (
          !claim.claim.first_name ||
          !claim.claim.last_name ||
          !claim.claim.tax_identifier
        ) {
          throw new Error("Claim is missing a first name, last name, or SSN.");
        }

        fineos.searchClaimantSSN(claim.claim.tax_identifier);
        fineos.clickBottomWidgetButton("OK");
        fineos.assertOnClaimantPage(
          claim.claim.first_name,
          claim.claim.last_name
        );
        const [startDate, endDate] = extractLeavePeriod(claim.claim);
        fineos.createNotification(startDate, endDate, "military care leave");
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
  it("I should receive an 'application started' notification", () => {
    cy.unstash<ApplicationRequestBody>("claim").then((claim) => {
      cy.unstash<Submission>("submission").then((submission) => {
        const employeeFullName = `${claim.first_name} ${claim.last_name}`;
        cy.log(employeeFullName);
        const subject = email.getNotificationSubject(
          employeeFullName,
          "application started",
          submission.fineos_absence_id
        );
        cy.log(subject);
        cy.task<Email[]>(
          "getEmails",
          {
            address: "gqzap.notifications@inbox.testmail.app",
            messageWildcard: submission.fineos_absence_id,
            subject: subject,
            timestamp_from: submission.timestamp_from,
          },
          { timeout: 360000 }
        ).then(async (emails) => {
          const data = email.getNotificationData(emails[0].html);
          expect(data.name).to.equal(employeeFullName);
          expect(data.applicationId).to.equal(submission.fineos_absence_id);
        });
      });
    });
  });
});
