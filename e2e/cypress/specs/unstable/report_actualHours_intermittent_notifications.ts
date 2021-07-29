import { fineos, portal, email, fineosPages } from "../../actions";
import { getFineosBaseUrl } from "../../config";
import { Submission } from "../../../src/types";
import { waitForAjaxComplete } from "../../actions/fineos";
import { addDays, formatISO, startOfWeek, subDays } from "date-fns";

describe("Report of intermittent leave hours notification", () => {
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
        }).then(({ fineos_absence_id, application_id }) => {
          cy.stash("submission", {
            application_id,
            fineos_absence_id,
            timestamp_from: Date.now(),
          });
          const claimPage = fineosPages.ClaimPage.visit(fineos_absence_id);
          claimPage.shouldHaveStatus("Eligibility", "Met");
          claimPage
            .adjudicate((adjudication) => {
              adjudication
                .evidence((evidence) => {
                  claim.documents.forEach(({ document_type }) =>
                    evidence.receive(document_type)
                  );
                })
                .certificationPeriods((certPeriods) => certPeriods.prefill())
                .acceptLeavePlan();
            })
            .approve();
          waitForAjaxComplete();
          // Those are the specific dates fit to the scenario spec.
          // We need those so that fineos approves the actual leave time and generates payments
          const mostRecentSunday = startOfWeek(new Date());
          const actualLeaveStart = formatISO(subDays(mostRecentSunday, 13), {
            representation: "date",
          });
          const actualLeaveEnd = formatISO(
            addDays(subDays(mostRecentSunday, 13), 4),
            {
              representation: "date",
            }
          );

          new fineosPages.ClaimPage().recordActualLeave((recordActualTime) => {
            // cy.log(actualLeaveStart, actualLeaveEnd);
            // cy.log(JSON.stringify(claim.claim, null, 2));
            // cy.pause();
            if (claim.metadata?.spanHoursStart && claim.metadata?.spanHoursEnd)
              recordActualTime.fillTimePeriod({
                startDate: actualLeaveStart,
                endDate: actualLeaveEnd,
                // Just casting to string instead of asserting here.
                timeSpanHoursStart: claim.metadata.spanHoursStart + "",
                timeSpanHoursEnd: claim.metadata.spanHoursEnd + "",
              });
            return recordActualTime.nextStep((additionalReporting) => {
              additionalReporting
                .reportAdditionalDetails({
                  reported_by: "Employee",
                  received_via: "Phone",
                  accepted: "Yes",
                })
                .finishRecordingActualLeave();
            });
          });
        });
      });
    }
  );

  it(
    "Employer should receive a '{Employee Name} reported their intermittent leave hours' notification",
    { retries: 0 },
    () => {
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
            .then(() => {
              const dob =
                claim.date_of_birth?.replace(/-/g, "/").slice(5) + "/****";
              cy.contains(dob);
              cy.contains(employeeFullName);
              cy.contains(submission.fineos_absence_id);
            });
        });
      });
    }
  );
});
