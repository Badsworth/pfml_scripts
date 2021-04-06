import { email } from "../../../tests/common/actions";
import { bailIfThisTestFails } from "../../../tests/common/before";
import { ApplicationResponse } from "../../../../src/api";
import { Submission } from "../../../../src/types";

describe(
  "Testing email notificaitons sent for both employee & employer after initial submission w/documents",
  { retries: 0 },
  () => {
    it("Submitting a bonding claim via the API (BHAP1)", () => {
      bailIfThisTestFails();
      cy.task("generateClaim", "BHAP1").then({ timeout: 40000 }, (claim) => {
        cy.stash("claim", claim.claim);
        cy.log("submitting", claim);
        cy.task("submitClaimToAPI", claim)
          .then((responseData: unknown) => responseData as ApplicationResponse)
          .then((responseData) => {
            cy.stash("submission", {
              application_id: responseData.application_id,
              fineos_absence_id: responseData.fineos_absence_id,
              timestamp_from: Date.now(),
            });
          });
      });
    });

    it("I should receive a 'Thank you for successfully submitting your ... application' notification (employee)", () => {
      cy.unstash<Submission>("submission").then((submission) => {
        cy.task<Email[]>(
          "getEmails",
          {
            address: "gqzap.notifications@inbox.testmail.app",
            subject:
              "Thank you for successfully submitting your Paid Family and Medical Leave Application",
            timestamp_from: submission.timestamp_from,
            messageWildcard: submission.fineos_absence_id,
            debugInfo: { "Fineos Claim ID": submission.fineos_absence_id },
          },
          { timeout: 180000 }
        ).should("not.be.empty");
      });
    });

    it("I should receive an 'application started' notification (employer)", () => {
      cy.unstash<ApplicationRequestBody>("claim").then((claim) => {
        cy.unstash<Submission>("submission").then((submission) => {
          const employeeFullName = `${claim.first_name} ${claim.last_name}`;
          const subject = email.getNotificationSubject(
            employeeFullName,
            "application started",
            submission.fineos_absence_id
          );
          cy.task<Email[]>(
            "getEmails",
            {
              address: "gqzap.notifications@inbox.testmail.app",
              subject: subject,
              timestamp_from: submission.timestamp_from,
              messageWildcard: submission.fineos_absence_id,
              debugInfo: { "Fineos Claim ID": submission.fineos_absence_id },
            },
            { timeout: 180000 }
          ).then(async (emails) => {
            const data = email.getNotificationData(emails[0].html);
            const dob =
              claim.date_of_birth?.replace(/-/g, "/").slice(5) + "/****";
            expect(data.name).to.equal(employeeFullName);
            expect(data.dob).to.equal(dob);
            expect(data.applicationId).to.equal(submission.fineos_absence_id);
          });
        });
      });
    });
  }
);
