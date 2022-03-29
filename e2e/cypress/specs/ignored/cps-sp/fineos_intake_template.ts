import { fineos, portal } from "../../../actions";
import { assertValidClaim } from "../../../../src/util/typeUtils";
import {
  AbsenceReasonDescription,
  ClaimantPage,
  ClaimPage,
  PrimaryRelationshipDescription,
} from "../../../actions/fineos.pages";
import { LeaveType } from "../../../actions/portal";
import { Submission } from "../../../../src/types";
import {
  extractLeavePeriodType,
  getLeavePeriod,
} from "../../../../src/util/claims";
import { waitForAjaxComplete } from "../../../actions/fineos";
import { LeaveReason } from "../../../../src/generation/Claim";
import faker from "faker";
import { add, format } from "date-fns";
import { config } from "../../../actions/common";

const getLeaveType = (leaveReason: NonNullable<LeaveReason>): LeaveType => {
  const mapping: {
    [key in NonNullable<LeaveReason>]: LeaveType;
  } = {
    "Military Exigency Family": "Active duty",
    "Child Bonding": "Bond with a child",
    "Pregnancy/Maternity": "Medical leave for pregnancy or birth",
    "Care for a Family Member": "Care for a family member",
    "Military Caregiver": "Military family",
    "Serious Health Condition - Employee": "Medical leave",
  };
  return mapping[leaveReason];
};

const getPrimaryRelationshipDescription = (
  leaveReason: NonNullable<LeaveReason>
): PrimaryRelationshipDescription | null => {
  const mapping: {
    [key in NonNullable<LeaveReason>]: PrimaryRelationshipDescription | null;
  } = {
    "Care for a Family Member": {
      relationship_to_employee: "Sibling - Brother/Sister",
      qualifier_1: "Biological",
    },
    "Child Bonding": {
      relationship_to_employee: "Sibling - Brother/Sister",
      qualifier_1: "Biological",
    },
    "Military Caregiver": {
      relationship_to_employee: "Sibling - Brother/Sister",
      qualifier_1: "Biological",
    },
    "Military Exigency Family": {
      relationship_to_employee: "Sibling - Brother/Sister",
      qualifier_1: "Biological",
    },
    "Pregnancy/Maternity": null,
    "Serious Health Condition - Employee": null,
  };

  return mapping[leaveReason];
};

const getAbsenceDescription = (
  leaveReason: NonNullable<LeaveReason>
): AbsenceReasonDescription => {
  const mapping: {
    [key in NonNullable<LeaveReason>]: Omit<AbsenceReasonDescription, "reason">;
  } = {
    "Care for a Family Member": {
      typeOfRequest: "Caring for a family member",
      relates_to: "Family",
      qualifier_1: "Serious Health Condition",
    },
    "Child Bonding": {
      typeOfRequest:
        "Bonding with a new child (adoption/ foster care/ newborn)",
      relates_to: "Family",
      qualifier_1: "Foster Care",
    },
    "Military Caregiver": {
      typeOfRequest: "Out of work for another reason",
      relates_to: "Family",
    },
    "Military Exigency Family": {
      typeOfRequest: "Out of work for another reason",
      relates_to: "Family",
      qualifier_1: "Other Additional Activities",
    },
    "Pregnancy/Maternity": {
      typeOfRequest: "Pregnancy, birth or related medical treatment",
      relates_to: "Employee",
      qualifier_1: "Birth Disability",
    },
    "Serious Health Condition - Employee": {
      typeOfRequest:
        "Sickness, treatment required for a medical condition or any other medical procedure",
      relates_to: "Employee",
      qualifier_1: "Not Work Related",
      qualifier_2: "Sickness",
    },
  };

  return {
    reason: leaveReason,
    ...mapping[leaveReason],
  };
};

// It's safe to use 'any' for a user-defined type guard like this
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const isLeaveReason = (value: any): value is NonNullable<LeaveReason> => {
  const mapping: {
    [key in NonNullable<LeaveReason>]: true;
  } = {
    "Military Exigency Family": true,
    "Child Bonding": true,
    "Pregnancy/Maternity": true,
    "Care for a Family Member": true,
    "Military Caregiver": true,
    "Serious Health Condition - Employee": true,
  };
  return value in mapping;
};

/**
 * Information on how to test CPS-906 tickets is here: https://github.com/EOLWD/pfml/blob/main/e2e/docs/cps-testing.md
 */
describe("Submit a claim through Fineos intake process, verify the Absence Case", () => {
  const claimSubmission =
    it("As a claimant, I should be able to submit a claim through Fineos intake", () => {
      fineos.before();
      cy.task("generateClaim", "MIL_EXI").then((claim) => {
        assertValidClaim(claim.claim);
        cy.stash("claim", claim);
        // Go to the claimant page
        ClaimantPage.visit(claim.claim.tax_identifier)
          // Adding date of birth and address for Claimants.
          .addAddress({
            city: faker.address.city(),
            state: "MA",
            zip: faker.address.zipCode(),
            line_1: faker.address.streetAddress(),
          })
          .editPersonalIdentification(
            {
              date_of_birth: format(
                faker.date.between(
                  add(new Date(), { years: -65 }),
                  add(new Date(), { years: -18 })
                ),
                "MM/dd/yyyy"
              ),
            },
            config("HAS_APRIL_UPGRADE") === "true" ? true : false
          )
          // Start intake process
          .startCreateNotification((occupationDetails) => {
            // @TODO CPS-906-P (CPS-1650)/Check that you can't submit 0 as amount of hours worked per week
            // Comment out everything after this to end the test.
            // occupationDetails.enterHoursWorkedPerWeek(0);
            // occupationDetails.clickNext();
            // fineos.assertErrorMessage("Hours worked per week must be entered");
            // @TODO end of testing CPS-906-P (CPS-1650)
            // Adjust as needed
            if (claim.claim.hours_worked_per_week)
              occupationDetails.enterHoursWorkedPerWeek(
                claim.claim.hours_worked_per_week
              );

            if (!isLeaveReason(claim.claim.leave_details?.reason)) {
              throw new Error(
                `Unexpected leave reason: ${claim.claim.leave_details?.reason}`
              );
            }
            const leaveReason = claim.claim.leave_details
              ?.reason as NonNullable<LeaveReason>;
            cy.stash("leaveReason", leaveReason);
            const absenceDescription = getAbsenceDescription(leaveReason);
            const primaryRelationshipDescription =
              getPrimaryRelationshipDescription(leaveReason);
            //By returning something from the callback, you can bubble it up to outside scope.
            return occupationDetails.nextStep((notificationOptions) =>
              notificationOptions
                // Request types
                .chooseTypeOfRequest(
                  absenceDescription.typeOfRequest ??
                    "Out of work for another reason"
                )
                .nextStep((reasonOfAbsence) => {
                  reasonOfAbsence.fillAbsenceReason(absenceDescription);
                  if (primaryRelationshipDescription) {
                    reasonOfAbsence.fillAbsenceRelationship(
                      primaryRelationshipDescription
                    );
                  }
                  return reasonOfAbsence.nextStep((datesOfAbsence) => {
                    assertValidClaim(claim.claim);
                    const [startDate, endDate] = getLeavePeriod(
                      claim.claim.leave_details
                    );
                    const leavePeriodType = extractLeavePeriodType(
                      claim.claim.leave_details
                    );
                    datesOfAbsence.toggleLeaveScheduleSlider(
                      extractLeavePeriodType(claim.claim.leave_details)
                    );
                    switch (leavePeriodType) {
                      case "Continuous":
                        datesOfAbsence.addFixedTimeOffPeriod({
                          status: "Known",
                          start: startDate,
                          end: endDate,
                        });
                        break;
                      case "Reduced Schedule": {
                        if (
                          claim.claim.leave_details
                            .reduced_schedule_leave_periods
                        )
                          datesOfAbsence.addReducedSchedulePeriod(
                            "Known",
                            claim.claim.leave_details
                              .reduced_schedule_leave_periods[0]
                          );
                        else
                          throw Error("Failed to add reduced leave schedule");
                        break;
                      }
                      default:
                        datesOfAbsence.addIntermittentLeavePeriod(
                          startDate,
                          endDate
                        );
                        break;
                    }
                    return datesOfAbsence.nextStep((workAbsenceDetails) =>
                      // @TODO CPS-906-AA (CPS-2579)
                      workAbsenceDetails
                        // @TODO selectWorkPatternType changed from Fixed to Unknown
                        .selectWorkPatternType("Fixed")
                        // @TODO comment out applyStandardWorkWeek() and return wrapUp.finishNotificationCreation() and below that line.
                        .applyStandardWorkWeek()
                        .nextStep((wrapUp) => {
                          if (leaveReason === "Military Caregiver") {
                            workAbsenceDetails.addMilitaryCaregiverDescription();
                          }
                          wrapUp.selectWithholdingPreference(
                            claim.is_withholding_tax
                          );
                          wrapUp.clickNext();

                          if (leaveReason === "Pregnancy/Maternity") {
                            // handle the extra step in pregnancy cases
                            wrapUp.clickNext();
                          }
                          // @TODO Uncomment the fineos.assertErrorMessage to check for error message
                          // fineos.assertErrorMessage("Work Pattern must be populated. Total hours per week in the Work Pattern must equal the Hours Worked Per Week field. Populate the Work Pattern and click Apply to Calendar before proceeding.")
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
            claimPage.notes((notes) => {
              cy.get("#widgetListMenu")
                .findByText("Create New")
                .click({ force: true });
              const selector =
                "#widgetListMenu .right-side-drop li:nth-child(2)";
              cy.get(selector)
                .findByText("Leave Request Review", {
                  selector: "span",
                })
                .click();
              waitForAjaxComplete();
              // Can't seem to be able to get inspect the alert properly here
              // So just checking that the limit works.
              cy.get(`#CaseNotesPopupWidgetAdd_PopupWidgetWrapper`)
                .should("be.visible")
                .within(() => {
                  // Input 4000 chars
                  cy.findByLabelText("Review note")
                    .type("aaaa".repeat(1000))
                    .should((el) =>
                      expect(el.val()).to.eq("aaaa".repeat(1000))
                    );

                  // Input few more chars, should still be at 4000.
                  cy.findByLabelText("Review note").type("a", { delay: 10 });
                  cy.findByLabelText("Review note").type("a", { delay: 10 });
                  cy.findByLabelText("Review note")
                    .type("a", { delay: 10 })
                    .should((el) =>
                      expect(el.val()).to.eq("aaaa".repeat(1000))
                    );
                  cy.findByText("OK").click();
                  waitForAjaxComplete();
                });
              notes.assertHasNote("Leave Request Review", "a".repeat(4000));
            });
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
    });

  it("LA can review and approve the claim", () => {
    cy.dependsOnPreviousPass([claimSubmission]);
    portal.before();
    cy.unstash<DehydratedClaim>("claim").then(({ claim }) => {
      cy.unstash<Submission>("submission").then((submission) => {
        cy.unstash<NonNullable<LeaveReason>>("leaveReason").then(
          (leaveReason) => {
            assertValidClaim(claim);
            portal.loginLeaveAdmin(claim.employer_fein);
            // Access the review page
            portal.visitActionRequiredERFormPage(submission.fineos_absence_id);
            // Deny the claim
            portal.assertLeaveType(getLeaveType(leaveReason));
            portal.respondToLeaveAdminRequest(false, true, false, false);
          }
        );
      });
    });
  });
});
