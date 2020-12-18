import { email } from "../../../tests/common/actions";
import { ApplicationResponse } from "../../../../src/api";

describe("Start Application Notification", () => {
  it("Should send a notification after I start an application in the portal", () => {
    const timestamp_from = Date.now();
    cy.task("generateClaim", {
      claimType: "BHAP1",
      employeeType: "financially eligible",
    }).then((claim: SimulationClaim) => {
      cy.log("Generated claim", claim.claim);
      const employeeFullName = `${claim.claim.first_name} ${claim.claim.last_name}`;
      const subject = email.getNotificationSubject(
        employeeFullName,
        "application started"
      );
      cy.task("submitClaimToAPI", claim)
        .then((responseData: unknown) => responseData as ApplicationResponse)
        .then((responseData) => {
          cy.task<Email[]>(
            "getEmails",
            {
              address: "gqzap.notifications@inbox.testmail.app",
              subject: subject,
              timestamp_from,
            },
            { timeout: 180000 }
          ).then((emails) => {
            const emailContent = email.getNotificationData(emails[0].html);
            if (typeof claim.claim.date_of_birth !== "string") {
              throw new Error("DOB must be a string");
            }
            const dob =
              claim.claim.date_of_birth.replace(/-/g, "/").slice(5) + "/****";
            expect(emailContent.name).to.equal(employeeFullName);
            expect(emailContent.dob).to.equal(dob);
            expect(emailContent.applicationId).to.equal(
              responseData.fineos_absence_id
            );
            expect(emails.length).to.be.greaterThan(0);
          });
        });
    });
  });
});
