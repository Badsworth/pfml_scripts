import { fineos, portal } from "../../../actions";
import { getFineosBaseUrl, getLeaveAdminCredentials } from "../../../config";
import { assertValidClaim } from "../../../../src/util/typeUtils";
import {
  AbsenceReasonDescription,
  ClaimantPage,
  ClaimPage,
} from "../../../actions/fineos.pages";
import { Submission } from "../../../../src/types";
import { getLeavePeriod } from "../../../../src/util/claims";

/**
 * Because there's too many scenarios for us to reasonably handle during the `Reason of Absence` step,
 * specify the description here and use/expand it as needed.
 */
const absenceDescription: AbsenceReasonDescription = {
  relates_to: "Family",
  // relates_to: "Employee",
  reason: "Military Exigency Family",
  // reason: "Military Caregiver",
  qualifier_1: "Other Additional Activities",
  // qualifier_1: "Active Duty",
  qualifier_2: "Sickness/Injury",
  // @todo Add more of you need to.
};

describe("Submit a claim through Fineos intake process, verify the Absence Case", () => {
  const claimSubmission = it(
    "As a claimant, I should be able to submit a claim through Fineos intake",
    { baseUrl: getFineosBaseUrl() },
    () => {
      fineos.before();
      cy.visit("/");
      cy.task("generateClaim", "MIL_EXI").then((claim) => {
        assertValidClaim(claim.claim);
        cy.stash("claim", claim);
        // Go to the claimant page
        ClaimantPage.visit(claim.claim.tax_identifier)
          // Start intake process
          .startCreateNotification((occupationDetails) => {
            // Adjust as needed
            if (claim.claim.hours_worked_per_week)
              occupationDetails.enterHoursWorkedPerWeek(
                claim.claim.hours_worked_per_week
              );
            //By returning something from the callback, you can bubble it up to outside scope.
            return occupationDetails.nextStep((notificationOptions) =>
              notificationOptions
                // Request types
                .chooseTypeOfRequest("Out of work for another reason")
                .nextStep((reasonOfAbsence) => {
                  cy.pause();
                  reasonOfAbsence.fillAbsenceReason(absenceDescription);
                  /* 
                    // @TODO Fill absence relationship for caring leave or bonding claims
                    .fillAbsenceRelationship({

                    })
                     */ return reasonOfAbsence.nextStep(
                    (datesOfAbsence) => {
                      assertValidClaim(claim.claim);

                      const [startDate, endDate] = getLeavePeriod(
                        claim.claim.leave_details
                      );
                      if (claim.claim.has_continuous_leave_periods)
                        // @TODO adjust leave period/status as needed
                        datesOfAbsence
                          .toggleLeaveScheduleSlider("continuos")
                          .addFixedTimeOffPeriod({
                            status: "Known",
                            start: startDate,
                            end: endDate,
                          });
                      if (claim.claim.has_intermittent_leave_periods)
                        // @TODO adjust leave period/status as needed
                        datesOfAbsence
                          // @TODO add method to add intermittent leave period
                          .toggleLeaveScheduleSlider("intermittent");
                      if (
                        claim.claim.has_reduced_schedule_leave_periods &&
                        claim.claim.leave_details.reduced_schedule_leave_periods
                      )
                        // @TODO adjust leave period/status as needed
                        datesOfAbsence
                          .toggleLeaveScheduleSlider("continuos")
                          .addReducedSchedulePeriod(
                            "Known",
                            claim.claim.leave_details
                              .reduced_schedule_leave_periods[0]
                          );
                      return datesOfAbsence.nextStep((workAbsenceDetails) =>
                        workAbsenceDetails
                          .selectWorkPatternType("Fixed")
                          .applyStandardWorkWeek()
                          .nextStep((wrapUp) => {
                            wrapUp.clickNext();
                            // Bubble up Leave Case id number to outside scope
                            return wrapUp.finishNotificationCreation();
                          })
                      );
                    }
                  );
                })
            );
          })
          .then((fineos_absence_id) => {
            cy.log(fineos_absence_id);
            cy.stash("submission", { fineos_absence_id });

            ClaimPage.visit(fineos_absence_id).adjudicate((adjudication) => {
              adjudication.evidence((evidence) => {
                claim.documents.forEach((doc) =>
                  evidence.receive(doc.document_type)
                );

                // Military exigency unsupported docs
                evidence.receive("Military exigency form");
                evidence.receive("Family Member Active Duty Service Proof");
              });
            });
          });
      });
    }
  );

  it("LA can review and approve the claim", () => {
    cy.dependsOnPreviousPass([claimSubmission]);
    portal.before();
    cy.unstash<DehydratedClaim>("claim").then(({ claim }) => {
      cy.unstash<Submission>("submission").then((submission) => {
        assertValidClaim(claim);
        portal.login(getLeaveAdminCredentials(claim.employer_fein));
        // Access the review page
        portal.visitActionRequiredERFormPage(submission.fineos_absence_id);
        // Deny the claim
        portal.assertLeaveType("Active duty");
        portal.respondToLeaveAdminRequest(false, true, false, false);
      });
    });
  });
});
