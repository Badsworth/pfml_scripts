import { fineos } from "../../../actions";
import { getFineosBaseUrl } from "../../../config";
import { assertValidClaim } from "../../../../src/util/typeUtils";
import {
  AbsenceReasonDescription,
  ClaimantPage,
  ClaimPage,
  PrimaryRelationshipDescription,
} from "../../../actions/fineos.pages";
import { addDays, formatISO, startOfWeek, subWeeks } from "date-fns";
import { getLeavePeriod } from "../../../../src/util/claims";

// Top level env override to use old employees/employers
Cypress.env({
  E2E_EMPLOYEES_FILE: "./employees/e2e-2021-06-30.json",
  E2E_EMPLOYERS_FILE: "./employers/e2e-2021-06-30.json",
});
/**
 * Because each scenario needs to have a specific amount of days and employment status. These will be separated as blocks so make sure to comment in and out.
 * We will need to use a specific data set for these scenario either ones we created or old data set, because of the changes we are making. If these test
 * scenarios were used current data set we need to make sure we fix the employment status back to "Active"
 **/

const absenceDescription: AbsenceReasonDescription = {
  relates_to: "Employee",
  reason: "Serious Health Condition - Employee",
  qualifier_1: "Not Work Related",
};
/**
 * Same as above, there's too many scenarios for us to reasonably handle when describing primary relationship,
 * specify the description here and use/expand it as needed. e.g. (Bonding with a child, Caring for a family member,
 * and Out of work for another reason)
 */
const _relationshipDescription: PrimaryRelationshipDescription = {
  relationship_to_employee: "Sibling - Brother/Sister",
  qualifier_1: "Biological",
};

// @todo This section can be used for CPS-906-C and 2 test cases scenarios.
/**
 * The CPS-906-C Test case 1 - Check alert for a claimant cannot apply more than 60 calendar days
 * in advance of the leave start date. An alert with withdraw the case is shown.
 * Test Case 2 - Check alert for a claimant cannot apply for leave retroactively/past
 * leave more than 90 calendar day. An alert with deny the case is shown.
 */
// describe("Submit a claim through Fineos intake process, check the alert message", () => {
//   it(
//     "As a claimant, I should be able to submit a claim through Fineos intake process",
//     () => {
//       fineos.before();
//       // @todo Reusing the CPS_SP this way easier to adjust the dates.
//       cy.task("generateClaim", "CPS_SP").then((claim) => {
//         assertValidClaim(claim.claim);
//         cy.stash("claim", claim);
//         // @todo This can be used for CPS-906-C, but make sure to comment out one message.
//         ClaimantPage.visit(claim.claim.tax_identifier).startCreateNotification(
//           (occupationDetails) => {
//             if (claim.claim.hours_worked_per_week)
//               occupationDetails.enterHoursWorkedPerWeek(
//                 claim.claim.hours_worked_per_week
//               );
//             return occupationDetails.nextStep((notificationOptions) =>
//               notificationOptions
//                 // Request types
//                 .chooseTypeOfRequest(
//                   "Sickness, treatment required for a medical condition or any other medical procedure"
//                 )
//                 .nextStep((reasonOfAbsence) => {
//                   reasonOfAbsence.fillAbsenceReason(absenceDescription);
//                   return reasonOfAbsence.nextStep((datesOfAbsence) => {
//                     assertValidClaim(claim.claim);

//                     // const [startDate, endDate] = getLeavePeriod(
//                     //   claim.claim.leave_details

//                     const mostRecentSunday = startOfWeek(new Date());
//                     const startDate = formatISO(addDays(mostRecentSunday, 70), {
//                       representation: "date",
//                     });
//                     const endDate = formatISO(addDays(mostRecentSunday, 90), {
//                       representation: "date",
//                     });
//                     if (claim.claim.has_continuous_leave_periods)
//                       // @TODO adjust leave period/status as needed
//                       datesOfAbsence
//                         .toggleLeaveScheduleSlider("continuos")
//                         .addFixedTimeOffPeriod({
//                           status: "Known",
//                           start: startDate,
//                           end: endDate,
//                         });
//                     return datesOfAbsence.nextStep((workAbsenceDetails) =>
//                       workAbsenceDetails
//                         .selectWorkPatternType("Fixed")
//                         .applyStandardWorkWeek()
//                         .nextStep((wrapUp) => {
//                           wrapUp.clickNext();
//                           // Bubble up Leave Case id number to outside scope
//                           return wrapUp.finishNotificationCreation();
//                         })
//                     );
//                   });
//                 })
//                 .then((fineos_absence_id) => {
//                   cy.log(fineos_absence_id);
//                   cy.stash("submission", { fineos_absence_id });
//                   const page = ClaimPage.visit(fineos_absence_id);
//                   // Check alert for CPS-906-C a claimant cannot apply more than 60 calendar days
//                   // in advance of the leave start date.
//                   cy.screenshot();
//                   page.alerts((alertsPage) => {
//                     alertsPage.assertAlertMessage(
//                       true,
//                       "Withdraw case. Claimant has filed their application more than 60 calendar days in advance of their Leave Start Date."
//                     );
//                     cy.screenshot();
//                   });
//                   // Check alert for CPS-906-C a claimant cannot apply for leave retroactively/past
//                   // leave more than 90 calendar day.
//                   // cy.screenshot();
//                   // page.alerts((alertsPage) => {
//                   //   alertsPage.assertAlertMessage(
//                   //     true,
//                   //     "Deny case due to 'Claim filed >90 days after leave began'. Claimant has filed their application more than 90 calendar days after their Leave Start Date")
//                   //   cy.screenshot()
//                   // })
//                 })
//             );
//           }
//         );
//       });
//     }
//   );
// });

// @todo This section can be used for CPS-906-E.
/**
 * The CPS-906-E is testing an Employee who is self-employed. We testing with a Care for Family
 * Member leave type. This should show an alert saying the employment status is self-employed.
 */
// describe("Submit a claim through Fineos intake process, check the alert message", () => {
//   it(
//     "As a claimant, I should be able to submit a claim through Fineos intake process",
//     () => {
//       fineos.before();
//       // @todo Adjust the CPS_SP to use "Care for Family Member" in this scenario
//       cy.task("generateClaim", "CPS_SP").then((claim) => {
//         assertValidClaim(claim.claim);
//         cy.stash("claim", claim);
//         ClaimantPage.visit(claim.claim.tax_identifier)
//           .startCreateNotification((occupationDetails) => {
//             occupationDetails.employmentStatus("Self-Employed");
//             cy.screenshot();
//             if (claim.claim.hours_worked_per_week)
//               occupationDetails.enterHoursWorkedPerWeek(
//                 claim.claim.hours_worked_per_week
//               );
//             return occupationDetails.nextStep((notificationOptions) =>
//               notificationOptions
//                 .chooseTypeOfRequest("Caring for a family member")
//                 .nextStep((reasonOfAbsence) => {
//                   reasonOfAbsence.fillAbsenceReason({
//                     relates_to: "Family",
//                     reason: "Care for a Family Member",
//                     qualifier_1: "Serious Health Condition",
//                   });
//                   reasonOfAbsence.fillAbsenceRelationship({
//                     relationship_to_employee: "Child",
//                     qualifier_1: "Biological",
//                   });
//                   return reasonOfAbsence.nextStep((datesOfAbsence) => {
//                     assertValidClaim(claim.claim);
//                     const [startDate, endDate] = getLeavePeriod(
//                       claim.claim.leave_details
//                     );
//                     if (claim.claim.has_continuous_leave_periods)
//                       // @TODO adjust leave period/status as needed
//                       datesOfAbsence
//                         .toggleLeaveScheduleSlider("continuos")
//                         .addFixedTimeOffPeriod({
//                           status: "Known",
//                           start: startDate,
//                           end: endDate,
//                         });
//                     datesOfAbsence.toggleLeaveScheduleSlider("continuos");
//                     return datesOfAbsence.nextStep((workAbsenceDetails) =>
//                       workAbsenceDetails
//                         .selectWorkPatternType("Fixed")
//                         .applyStandardWorkWeek()
//                         .nextStep((wrapUp) => {
//                           wrapUp.clickNext();
//                           // Bubble up Leave Case id number to outside scope
//                           return wrapUp.finishNotificationCreation();
//                         })
//                     );
//                   });
//                 })
//             );
//           })
//           .then((fineos_absence_id) => {
//             cy.log(fineos_absence_id);
//             cy.stash("submission", { fineos_absence_id });
//             const page = ClaimPage.visit(fineos_absence_id);
//             // Check alert for CPS-906-E for self-employed
//             cy.screenshot();
//             page.alerts((alertsPage) => {
//               alertsPage.assertAlertMessage(
//                 true,
//                 "Validation: Employment status is self-employed"
//               );
//               cy.screenshot();
//             });
//           });
//       });
//     }
//   );
// });

// @todo This section can be used for CPS-906-F. Reuse the absenceDescription above CPS-906-E
/**
 * The CPS-906-F Test case 1 - Alert on a case when a former employee applies for a leave that
 * starts more than 26 weeks after their job end date so we deny the claim due to ineligibility.
 * Test Case 2 - alert should appear on a case when Employment status = Terminated or Retired
 * and the Leave Start Date - Job End Date > 26 weeks.
 * Test Case 3 - No alert should show up when a former employee separated from employment,
 * not more than 26 weeks.
 */
describe("Submit a claim through Fineos intake process, check the alert message", () => {
  it("As a claimant, I should be able to submit a claim through Fineos intake process", () => {
    fineos.before();
    // @todo Adjust the CPS_SP to use "Care for Family Member" in this scenario
    cy.task("generateClaim", "CPS_SP").then((claim) => {
      assertValidClaim(claim.claim);
      cy.stash("claim", claim);
      ClaimantPage.visit(claim.claim.tax_identifier)
        .startCreateNotification((occupationDetails) => {
          const mostRecentSunday = startOfWeek(new Date());
          const jobEnded = formatISO(
            subWeeks(
              mostRecentSunday,
              // 27
              // Test case 3, separation less than 26 weeks before leave start
              10
            ),
            {
              representation: "date",
            }
          );
          // @todo adjust the employment status
          // Test case 1 and Test Case 3
          // occupationDetails.employmentStatus("Terminated");
          // Test case 2
          occupationDetails.employmentStatus("Retired");
          // @todo adjust the date when job ended
          occupationDetails.enterDateJobEnded(jobEnded);
          cy.screenshot();
          if (claim.claim.hours_worked_per_week)
            occupationDetails.enterHoursWorkedPerWeek(
              claim.claim.hours_worked_per_week
            );
          return occupationDetails.nextStep((notificationOptions) =>
            notificationOptions
              .chooseTypeOfRequest("Caring for a family member")
              .nextStep((reasonOfAbsence) => {
                reasonOfAbsence.fillAbsenceReason({
                  relates_to: "Family",
                  reason: "Care for a Family Member",
                  qualifier_1: "Serious Health Condition",
                });
                reasonOfAbsence.fillAbsenceRelationship({
                  relationship_to_employee: "Child",
                  qualifier_1: "Biological",
                });
                return reasonOfAbsence.nextStep((datesOfAbsence) => {
                  assertValidClaim(claim.claim);
                  const startDate = formatISO(mostRecentSunday, {
                    representation: "date",
                  });
                  const endDate = formatISO(addDays(mostRecentSunday, 7), {
                    representation: "date",
                  });
                  if (claim.claim.has_continuous_leave_periods)
                    // @TODO adjust leave period/status as needed
                    datesOfAbsence
                      .toggleLeaveScheduleSlider("continuos")
                      .addFixedTimeOffPeriod({
                        status: "Known",
                        start: startDate,
                        end: endDate,
                      });
                  datesOfAbsence.toggleLeaveScheduleSlider("continuos");
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
                });
              })
          );
        })
        .then((fineos_absence_id) => {
          cy.log(fineos_absence_id);
          cy.stash("submission", { fineos_absence_id });
          const page = ClaimPage.visit(fineos_absence_id);
          cy.screenshot();
          // @todo Test Case 1 and 2 have the same alert message.
          // page.alerts((alertsPage) => {
          //   alertsPage.assertAlertMessage(
          //     true,
          //     "Deny case due to 'Unemployment grace period expired.' Claimant reports being Unemployed/Terminated or Retired and their leave request Start Date is more than 26 weeks from their Date Job E.."
          //   );
          //   cy.screenshot();
          // });
          // @todo Test Case 3 no alert should show up when a former employee separated from employment, not more than 26 weeks.
          page.alerts((alertsPage) => {
            alertsPage.assertAlertMessage(false, "");
            cy.screenshot();
          });
        });
    });
  });
});
