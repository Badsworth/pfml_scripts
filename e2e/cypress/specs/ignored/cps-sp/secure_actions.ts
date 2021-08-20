import { fineos, fineosPages } from "../../../actions";
import { getFineosBaseUrl } from "../../../config";
import { Submission } from "../../../../src/types";
import { getSubmissionFromApiResponse } from "../../../../src/util/claims";
import { FineosSecurityGroups } from "../../../../src/submission/fineos.pages";
import { addDays, format, startOfWeek, subDays } from "date-fns";
import {
  clickBottomWidgetButton,
  waitForAjaxComplete,
} from "../../../actions/fineos";

const userSecurityGroup: FineosSecurityGroups = "DFML Claims Examiners(sec)";

describe("Historical absence secure actions", () => {
  it("Given a submitted claim", { baseUrl: getFineosBaseUrl() }, () => {
    fineos.before();
    cy.visit("/");
    //Submit a claim via the API, including Employer Response.
    cy.task("generateClaim", "CHAP_ER").then((claim) => {
      cy.stash("claim", claim);
      cy.task("submitClaimToAPI", claim).then((response) => {
        cy.stash("submission", getSubmissionFromApiResponse(response));
      });
    });
  });

  it(
    `${userSecurityGroup} can create historical absence case within Absence Case`,
    { baseUrl: getFineosBaseUrl() },
    () => {
      cy.unstash<DehydratedClaim>("claim").then((claim) => {
        cy.unstash<Submission>("submission").then(
          ({ application_id, fineos_absence_id }) => {
            fineos.before();
            cy.visit("/");
            cy.stash("claim", claim.claim);
            cy.stash("submission", {
              application_id: application_id,
              fineos_absence_id: fineos_absence_id,
              timestamp_from: Date.now(),
            });
            // Create historical absence
            const historicalAbsence =
              fineosPages.ClaimPage.visit(
                fineos_absence_id
              ).addHistoricalAbsenceCase();
            historicalAbsence.checkAvailability("19.00 Weeks");
            // Edit historical absence
            const mostRecentSunday = startOfWeek(new Date());
            const startDate = subDays(mostRecentSunday, 13);
            const endDateFormatted = format(
              addDays(startDate, 7),
              "MM/dd/yyyy"
            );
            historicalAbsence.editLeaveRequestDates({
              end: { date: endDateFormatted },
            });
            // Check for changed availability
            historicalAbsence.checkAvailability("18.80 Weeks");

            // Remove an absence period
            const newStartDate = subDays(mostRecentSunday, 5);
            const newStartDateFormatted = format(newStartDate, "MM/dd/yyyy");
            const newEndDateFormatted = format(
              addDays(newStartDate, 3),
              "MM/dd/yyyy"
            );
            // Here, because a historical case must always have at least one absence period
            // we need to add another absence period before testing for old one.
            historicalAbsence.addFixedTimePeriod({
              start: {
                date: newStartDateFormatted,
                all_day: true,
              },
              end: {
                date: newEndDateFormatted,
                all_day: true,
              },
            });
            cy.findByTitle("Edit Leave Request").click();
            fineos.onTab("Request Information");
            waitForAjaxComplete();
            cy.get("#timeOffHistoricalAbsencePeriodsListviewWidget")
              .findByTitle("Delete Historical Absence Period")
              .click();
            cy.contains("table.PopupBean", "Absence Period Change")
              .findByText("Yes")
              .click();
            cy.contains("table.PopupBean", "Delete Historical Absence Period")
              .findByText("Yes")
              .click();
            waitForAjaxComplete();
            clickBottomWidgetButton("OK");
            waitForAjaxComplete();
            // Check for changed avaiability again.
            historicalAbsence.checkAvailability("19.20 Weeks");
          }
        );
      });
    }
  );
});
