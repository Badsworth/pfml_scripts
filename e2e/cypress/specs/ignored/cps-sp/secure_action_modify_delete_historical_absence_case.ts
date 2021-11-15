import { fineos, fineosPages } from "../../../actions";
import { Submission } from "../../../../src/types";
import { getSubmissionFromApiResponse } from "../../../../src/util/claims";
import { FineosSecurityGroups } from "../../../../src/submission/fineos.pages";
import { addDays, format, startOfWeek, subDays } from "date-fns";
import {
  clickBottomWidgetButton,
  waitForAjaxComplete,
} from "../../../actions/fineos";
import { config, getFineosBaseUrl } from "../../../actions/common";

const ssoAccount2Credentials: Credentials = {
  username: config("SSO2_USERNAME"),
  password: config("SSO2_PASSWORD"),
};

const securityGroups: [FineosSecurityGroups, boolean][] = [
  ["DFML Claims Examiners(sec)", true],
  ["DFML Claims Supervisors(sec)", true],
  ["DFML Compliance Analyst(sec)", true],
  ["DFML Compliance Supervisors(sec)", true],
  ["DFML Appeals Administrator(sec)", true],
  ["DFML Appeals Examiner I(sec)", true],
  ["DFML Appeals Examiner II(sec)", true],
  ["SaviLinx Agents (sec)", false],
  ["SaviLinx Secured Agents(sec)", false],
  ["SaviLinx Supervisors(sec)", false],
  ["DFML IT(sec)", false],
];
// Set baseurl before running the spec.
Cypress.config("baseUrl", getFineosBaseUrl());

securityGroups.forEach(([userSecurityGroup, canUseSecureAction]) => {
  describe("Historical absence secure actions", () => {
    const claimSubmit = it("Given a submitted claim", () => {
      //Submit a claim via the API, including Employer Response.
      cy.task("generateClaim", "CHAP_ER").then((claim) => {
        cy.stash("claim", claim);
        cy.task("submitClaimToAPI", claim).then((response) => {
          cy.stash("submission", getSubmissionFromApiResponse(response));
          // Set the security group for second sso account.
          cy.task("chooseFineosRole", {
            userId: ssoAccount2Credentials.username,
            preset: userSecurityGroup,
            debug: false,
          });
        });
      });
    });

    it(`${userSecurityGroup} can${
      canUseSecureAction ? "" : "'t"
    } create/modify/delete historical absence case within Absence Case`, () => {
      // Login as second SSO account
      fineos.before(ssoAccount2Credentials);
      cy.dependsOnPreviousPass([claimSubmit]);
      cy.unstash<DehydratedClaim>("claim").then(() => {
        cy.unstash<Submission>("submission").then(({ fineos_absence_id }) => {
          // Expect failure if user can't perform secure action.
          cy.on("fail", (e) => {
            if (
              !canUseSecureAction &&
              e.message.includes(`Control is protected by a Secured Action.`)
            ) {
              console.log("Failed as expected");
            } else {
              throw e;
            }
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
          const endDateFormatted = format(addDays(startDate, 7), "MM/dd/yyyy");
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
        });
      });
    });
  });
});
