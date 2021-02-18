import { fineos, email } from "../../../../tests/common/actions";
import { beforeFineos } from "../../../../tests/common/before";
import { extractLeavePeriod } from "../../../../../src/utils";
import { getFineosBaseUrl } from "../../../../config";
import { Submission } from "../../../../../src/types";

describe("Create a new continuous leave, military caregiver claim in FINEOS", () => {
  it(
    "Should be able to create a claim",
    { baseUrl: getFineosBaseUrl() },
    () => {
      beforeFineos();
      cy.task("generateClaim", {
        claimType: "BHAP1",
        employeeType: "financially eligible",
      }).then((claim: SimulationClaim) => {
        cy.log("generated claim", claim.claim);
        cy.stash("claim", claim.claim);
        if (
          !claim.claim.first_name ||
          !claim.claim.last_name ||
          !claim.claim.tax_identifier
        ) {
          throw new Error("Claim is missing a first name, last name, or SSN.");
        }

        cy.visit("/");
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
            subject: subject,
            timestamp_from: submission.timestamp_from,
          },
          { timeout: 360000 }
        ).then(async (emails) => {
          const emailContent = await email.getNotificationData(
            emails[emails.length - 1].html
          );
          expect(emailContent.name).to.equal(employeeFullName);
          expect(emailContent.applicationId).to.equal(
            submission.fineos_absence_id
          );
        });
      });
    });
  });
});
