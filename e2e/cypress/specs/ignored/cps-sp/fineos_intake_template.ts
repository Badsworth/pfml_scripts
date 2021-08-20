import { fineos, portal } from "../../../actions";
import { getFineosBaseUrl, getLeaveAdminCredentials } from "../../../config";
import { assertValidClaim } from "../../../../src/util/typeUtils";
import {
  AbsenceReasonDescription,
  ClaimantPage,
  ClaimPage,
  PrimaryRelationshipDescription,
} from "../../../actions/fineos.pages";
import { Submission } from "../../../../src/types";
import { getLeavePeriod } from "../../../../src/util/claims";
import { waitForAjaxComplete } from "../../../actions/fineos";

/**
 * Because there's too many scenarios for us to reasonably handle during the `Reason of Absence` step,
 * specify the description here and use/expand it as needed.
 */
// @todo Depending on what leave type you are taking this will need to be updated.
const absenceDescription: AbsenceReasonDescription = {
  relates_to: "Family",
  // relates_to: "Employee",
  reason: "Military Exigency Family",
  // reason: "Military Caregiver",
  qualifier_1: "Other Additional Activities",
  // qualifier_1: "Active Duty",
  // qualifier_2: "Sickness/Injury",
};

/**
 * Same as above, there's too many scenarios for us to reasonably handle when describing primary relationship,
 * specify the description here and use/expand it as needed.
 */
// @todo If the Leave Type has Absence Relationship. This includes Child Bonding, Caring for a family member, and Out of work for another reason with Family.
const _relationshipDescription: PrimaryRelationshipDescription = {
  relationship_to_employee: "Sibling - Brother/Sister",
  qualifier_1: "Biological",
};

/**
 * Information on how to test CPS-906 tickets is here: https://github.com/EOLWD/pfml/blob/main/e2e/docs/cps-testing.md
 */
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
            // @TODO CPS-906-P (CPS-1650)/Check that you can't submit 0 as amount of hours worked per week
            // Comment out everything after this to end the test.
            occupationDetails.enterHoursWorkedPerWeek(0);
            occupationDetails.clickNext();
            fineos.assertErrorMessage("Hours worked per week must be entered");
            // @TODO end of testing CPS-906-P (CPS-1650)
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
                  reasonOfAbsence.fillAbsenceReason(absenceDescription);

                  // @TODO Fill absence relationship for caring leave or bonding claims
                  // .fillAbsenceRelationship(relationshipDescription);
                  return reasonOfAbsence.nextStep((datesOfAbsence) => {
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
                    // @TODO CPS-906-G (CPS-2449)/intermittent & reduced leave periods.
                    if (claim.claim.has_intermittent_leave_periods)
                      // @TODO adjust leave period/status as needed
                      datesOfAbsence
                        // @TODO add method to add intermittent leave period
                        .toggleLeaveScheduleSlider("intermittent")
                        .addIntermittentLeavePeriod(startDate, endDate);
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
                  });
                })
            );
          })
          .then((fineos_absence_id) => {
            cy.log(fineos_absence_id);
            cy.stash("submission", { fineos_absence_id });

            const claimPage = ClaimPage.visit(fineos_absence_id);
            // @TODO  testing CPS-906-D (CPS-794)/notes character limit
            // claimPage.notes((notes) => {
            //   cy.findByText("Create New").click();
            //   cy.findByText("Leave Request Review", {
            //     selector: "span",
            //   }).click();
            //   waitForAjaxComplete();
            //   // Can't seem to be able to get inspect the alert properly here
            //   // So just checking that the limit works.
            //   cy.get(`#CaseNotesPopupWidgetAdd_PopupWidgetWrapper`)
            //     .should("be.visible")
            //     .within(() => {
            //       // Input 4000 chars
            //       cy.findByLabelText("Review note")
            //         .type("aaaa".repeat(1000))
            //         .should((el) =>
            //           expect(el.val()).to.eq("aaaa".repeat(1000))
            //         );

            //       // Input few more chars, should still be at 4000.
            //       cy.findByLabelText("Review note").type("a", { delay: 10 });
            //       cy.findByLabelText("Review note").type("a", { delay: 10 });
            //       cy.findByLabelText("Review note")
            //         .type("a", { delay: 10 })
            //         .should((el) => expect(el.val()).to.eq("aaaa".repeat(1000)));
            //       cy.findByText("OK").click();
            //       waitForAjaxComplete();
            //     });
            //   notes.assertHasNote("Leave Request Review", "a".repeat(4000));
            // });
            // @TODO  End of testing CPS-906-D (CPS-794)

            claimPage.adjudicate((adjudication) => {
              adjudication.availability((_) => {
                cy.get(`tr.ListRowSelected`).should("be.visible");
                // @note CPS-906-H-0 (CPS-2449)/Checking for time increment config at "Availability" tab.
                cy.findByTitle(
                  "Manage time for the selected Leave Plan"
                ).click();
                waitForAjaxComplete();
                cy.findByText("Minimum time increment")
                  .parent()
                  .next()
                  .should("contain.text", "Does Not Apply");
                cy.findByText("Minimum time threshold")
                  .parent()
                  .next()
                  .should("contain.text", "Does Not Apply");
                cy.get("#footerButtonsBar input[value='Close']").click();
                waitForAjaxComplete();
              });
              // @TODO CPS-906-G (CPS-2449)/Check restriction decision
              adjudication.restrictions((restrictions) => {
                restrictions.assertRestrictionDecision("Passed");
              });
              adjudication.evidence((evidence) => {
                claim.documents.forEach((doc) => {
                  // @TODO CPS-906-H-0 (CPS-2449)
                  // @TODO CPS-906-V (CPS-2454)
                  // Checking for evidence and it's initial status as part of the adjudication.
                  evidence.assertEvidenceStatus({
                    evidenceType: doc.document_type,
                    decision: "Pending",
                    receipt: "Pending",
                  });
                  evidence.receive(doc.document_type);
                });
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
