import { fineos, portal, email, fineosPages } from "../../actions";
import { Submission } from "../../../src/types";
import { waitForAjaxComplete } from "../../actions/fineos";
import { addDays, formatISO, startOfWeek, subDays } from "date-fns";

describe("Report of intermittent leave hours notification", () => {
  after(() => {
    portal.deleteDownloadsFolder();
  });

  const submit = it("Can submit a claim via API", () => {
    cy.task("generateClaim", "BIAP60ER").then((claim) => {
      cy.stash("claim", claim);
      cy.task("submitClaimToAPI", claim).then(
        ({ fineos_absence_id, application_id }) => {
          cy.stash("submission", {
            application_id,
            fineos_absence_id,
            timestamp_from: Date.now(),
          });
        }
      );
    });
  });

  const approval =
    it("Given a fully approved claim and leave hours correctly recorded by CSR rep", () => {
      cy.dependsOnPreviousPass([submit]);
      cy.unstash<DehydratedClaim>("claim").then((claim) => {
        cy.unstash<Submission>("submission").then(({ fineos_absence_id }) => {
          fineos.before();
          cy.visit("/");
          const claimPage = fineosPages.ClaimPage.visit(fineos_absence_id);
          // This check safeguards us against failure cases where we try to approve an already approved claim.
          fineos.getClaimStatus().then((status) => {
            if (status === "Approved") return;
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
          });
        });
      });
    });

  const hoursRecorded =
    it("CSR Representative can record actual leave hours", () => {
      cy.dependsOnPreviousPass([submit, approval]);
      fineos.before();
      cy.unstash<DehydratedClaim>("claim").then((claim) => {
        cy.unstash<Submission>("submission").then(({ fineos_absence_id }) => {
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
          fineosPages.ClaimPage.visit(fineos_absence_id).recordActualLeave(
            (recordActualTime) => {
              if (
                claim.metadata?.spanHoursStart &&
                claim.metadata?.spanHoursEnd
              )
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
            }
          );
        });
      });
    });

  it(
    "Employer should receive a '{Employee Name} reported their intermittent leave hours' notification",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass([submit, approval, hoursRecorded]);
      cy.unstash<Submission>("submission").then((submission) => {
        cy.unstash<DehydratedClaim>("claim").then(({ claim }) => {
          const employeeFullName = `${claim.first_name} ${claim.last_name}`;
          const employerNotificationSubject = email.getNotificationSubject(
            "review leave hours",
            submission.fineos_absence_id
          );
          // Check email for Employer/Leave Admin
          email
            .getEmails(
              {
                address: "gqzap.notifications@inbox.testmail.app",
                subjectWildcard: employerNotificationSubject,
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
              email.assertValidSubject(
                `${claim.first_name} ${claim.last_name}`
              );
            });
        });
      });
    }
  );
});
