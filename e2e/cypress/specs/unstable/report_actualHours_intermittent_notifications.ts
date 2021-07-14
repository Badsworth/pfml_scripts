import { fineos, portal, email } from "../../actions";
import { getFineosBaseUrl } from "../../config";
import { Submission } from "../../../src/types";

describe(
  "Report of intermittent leave hours notification",
  { retries: 0 },
  () => {
    after(() => {
      portal.deleteDownloadsFolder();
    });

    const submit = it(
      "Given a fully approved claim and leave hours correctly recorded by CSR rep",
      { baseUrl: getFineosBaseUrl() },
      () => {
        fineos.before();
        cy.visit("/");
        // Submit a claim via the API, including Employer Response.
        cy.task("generateClaim", "BIAP60ER").then((claim) => {
          cy.stash("claim", claim.claim);
          cy.task("submitClaimToAPI", {
            ...claim,
          }).then((response) => {
            if (!response.fineos_absence_id) {
              throw new Error(
                "Response contained no fineos_absence_id property"
              );
            }

            cy.stash("submission", {
              application_id: response.application_id,
              fineos_absence_id: response.fineos_absence_id,
              timestamp_from: Date.now(),
            });
            fineos.intermittentClaimAdjudicationFlow(
              response.fineos_absence_id,
              "Child Bonding",
              true
            );
            fineos.submitIntermittentActualHours(
              claim.metadata?.spanHoursStart as string,
              claim.metadata?.spanHoursEnd as string
            );
          });
        });
      }
    );

    it("Employer should receive a '{Employee Name} reported their intermittent leave hours' notification", () => {
      cy.dependsOnPreviousPass([submit]);
      cy.unstash<Submission>("submission").then((submission) => {
        cy.unstash<ApplicationRequestBody>("claim").then((claim) => {
          const employeeFullName = `${claim.first_name} ${claim.last_name}`;
          const employerNotificationSubject = email.getNotificationSubject(
            `${claim.first_name} ${claim.last_name}`,
            "review leave hours",
            submission.fineos_absence_id
          );
          // Check email for Employer/Leave Admin
          email
            .getEmails(
              {
                address: "gqzap.notifications@inbox.testmail.app",
                subject: employerNotificationSubject,
                messageWildcard: submission.fineos_absence_id,
                timestamp_from: submission.timestamp_from,
                debugInfo: { "Fineos Claim ID": submission.fineos_absence_id },
              },
              180000
            )
            .then(async (emails) => {
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
