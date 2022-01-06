import { fineos, fineosPages } from "../../../actions";
import { assertValidClaim } from "../../../../src/util/typeUtils";
import { config } from "../../../actions/common";
import { addDays, formatISO, startOfWeek } from "date-fns";

//@TODO this can only be used in DT2/Test environment at the moment.
describe("Submit a claim through FINEOS with OrgUnit included", () => {
  it("Should be able to create a claim with an OrgUnit", () => {
    fineos.before();
    cy.task("generateClaim", {
      scenario: "ORGUNIT",
      employeePoolFileName: config("ORGUNIT_EMPLOYEES_FILE")
    }).then((claim) => {
      cy.stash("claim", claim);
      assertValidClaim(claim.claim);
      const department = claim.metadata
        ?.orgunits as unknown as string;
      const worksite = claim.metadata
        ?.worksite as unknown as string;
      // Step through the FINEOS intake form to adjust just for the OrgUnit changes.
      fineosPages.ClaimantPage.visit(claim.claim.tax_identifier)
        .startCreateNotification((occupationDetails) => {
          const mostRecentSunday = startOfWeek(new Date());
          occupationDetails.employmentStatus("Active")
          if (claim.claim.hours_worked_per_week)
            occupationDetails.enterHoursWorkedPerWeek(
              claim.claim.hours_worked_per_week
            );
          cy.get('a[id*="reportingAdminGroupDetailsIntakeWidget_un73_editAdminGroupLink"]')
            .click({force: true});
          cy.get('#reportingAdminGroupDetailsPopupWidget_PopupWidgetWrapper')
            .find("select")
            .select(`${worksite}-${department}`);
          cy.get("input[value='OK']").click({ force: true });
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
                  const endDate = formatISO(addDays(mostRecentSunday, 2), {
                    representation: "date",
                  });
                  if (claim.claim.has_continuous_leave_periods)
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
                        // Tax withholdings changes are part of the January release,
                        // which OrgUnits are as well so both are together in the FINEOS envs DT2 and cps-preview.
                        if (
                          config("FINEOS_HAS_UPDATED_WITHHOLDING_SELECTION") ===
                          "true"
                        ) {
                          fineos.waitForAjaxComplete();
                        }
                        cy.get(
                          "input[type='checkbox'][name$='_somSITFITVerification_CHECKBOX']"
                        ).click();
                        fineos.waitForAjaxComplete();
                        wrapUp.clickNext(20000);
                        return wrapUp.finishNotificationCreation();
                      })
                  );
                });
              })
          );
        })
        .then((fineos_absence_id) => {
          cy.log(fineos_absence_id);
          cy.stash("submission", {
            fineos_absence_id: fineos_absence_id,
            timestamp_from: Date.now(),
          });
          const status = fineosPages.ClaimPage.visit(fineos_absence_id)
          // Checking the General tab first.
          fineos.onTab("General");
          cy.get('#reportingAdminGroupDetailsWidget_un59_adminGroup').should(
            "contain.text", `${worksite}-${department}`);
          fineos.onTab("Absence Hub");
          // Checking the employee information in the Adjudicate section
          status.adjudicate(
            (adjudication) => {
              adjudication.requestEmploymentInformation()
              cy.get('span[id*="occupationDetailsProxy_un202_Organisation_Unit_Label"]')
                .should((element) => {
                    expect(
                      element,
                      `Organization Unit should be the ${department}`
                    ).to.have.text(`${department}`);
                  }
                );
            });
        });
    });
  });
});
