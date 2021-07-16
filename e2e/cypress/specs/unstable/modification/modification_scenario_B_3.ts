import { addDays, format, parse } from "date-fns";
import { fineos, fineosPages, portal } from "../../../actions";
import { getFineosBaseUrl, getLeaveAdminCredentials } from "../../../config";

import { ReducedScheduleLeavePeriods } from "../../../../src/_api";
import { Submission } from "../../../../src/types";
import { assertValidClaim } from "../../../../src/util/typeUtils";
import { extractLeavePeriod } from "../../../../src/util/claims";
import { getNotificationSubject } from "../../../actions/email";

// Covered by SOP 54

describe("Post-approval (notifications/notices)", () => {
  const credentials: Credentials = {
    username: Cypress.env("E2E_PORTAL_USERNAME"),
    password: Cypress.env("E2E_PORTAL_PASSWORD"),
  };
  const extension = it(
    "Given a fully approved claim, a CSR agent can extend the claim's leave dates",
    { baseUrl: getFineosBaseUrl() },
    () => {
      fineos.before();
      cy.visit("/");
      // Submit a claim via the API, including Employer Response.
      cy.task("generateClaim", "CHAP_REDUCED_ER").then((claim) => {
        cy.stash("claim", claim);
        cy.task("submitClaimToAPI", {
          ...claim,
          credentials,
        }).then((response) => {
          if (!response.fineos_absence_id) {
            throw new Error("Response contained no fineos_absence_id property");
          };
          if (claim.claim.leave_details == undefined){
            throw new Error("Leave Details undefined")
          }
          const leaveDetails = claim.claim.leave_details
          if (leaveDetails.reduced_schedule_leave_periods == undefined){
            throw new Error("Reduced Leave Periods are undefined")
          }
          const reducedLeaveDetails = leaveDetails.reduced_schedule_leave_periods[0]
          const decreaseMinutes = function(minutes: number | null | undefined){
            if (!!minutes && minutes >= 60){
              return minutes - 60
            } else {
              return minutes
            }
          };

          if (reducedLeaveDetails != undefined){
            reducedLeaveDetails.monday_off_minutes = decreaseMinutes(reducedLeaveDetails.thursday_off_minutes)
            reducedLeaveDetails.tuesday_off_minutes = decreaseMinutes(reducedLeaveDetails.thursday_off_minutes)
            reducedLeaveDetails.wednesday_off_minutes = decreaseMinutes(reducedLeaveDetails.thursday_off_minutes)
            reducedLeaveDetails.thursday_off_minutes = decreaseMinutes(reducedLeaveDetails.thursday_off_minutes)
            reducedLeaveDetails.friday_off_minutes = decreaseMinutes(reducedLeaveDetails.thursday_off_minutes)
            reducedLeaveDetails.saturday_off_minutes = decreaseMinutes(reducedLeaveDetails.thursday_off_minutes)
            reducedLeaveDetails.sunday_off_minutes = decreaseMinutes(reducedLeaveDetails.thursday_off_minutes)
          }

          cy.stash("submission", {
            application_id: response.application_id,
            fineos_absence_id: response.fineos_absence_id,
            timestamp_from: Date.now(),
          });
          cy.stash("decreasedReducedLeaveDetails", reducedLeaveDetails);
          const claimPage = fineosPages.ClaimPage.visit(
            response.fineos_absence_id
          );


          claimPage.adjudicate((adjudicate) =>
            adjudicate.enterReducedLeaveSchedule(reducedLeaveDetails)
          );

          // Including this visit helps to avoid the "Whoops there is no test to run" message by Cypress.
          cy.visit("/");
          const claimAfterExtension = fineosPages.ClaimPage.visit(
            response.fineos_absence_id
          );

          claimPage.adjudicate((adjudication) => {
            adjudication.evidence((evidence) => {
              for (const document of claim.documents) {
                evidence.receive(document.document_type);
              }
            });
            cy.wait("@ajaxRender");
            cy.wait(150);
            adjudication.certificationPeriods((certificationPeriods) =>
              certificationPeriods.prefill()
            );
            adjudication.acceptLeavePlan();
          });
        });
      });
    }
  );

  it(
    "Leave admin will see leave periods for the claim that reflect the extension",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass([extension]);
      portal.before();
      cy.visit("/");
      cy.unstash<DehydratedClaim>("claim").then(({ claim }) => {
        cy.unstash<Submission>("submission").then((submission) => {
          assertValidClaim(claim);
          portal.login(getLeaveAdminCredentials(claim.employer_fein));
          portal.visitActionRequiredERFormPage(submission.fineos_absence_id)
        }
      );
    });
  });
  it("As a leave admin, I should receive a request for information email", () => {
    cy.dependsOnPreviousPass([extension]);
    cy.unstash<Submission>("submission").then(
      ({ timestamp_from, fineos_absence_id }) => {
        cy.unstash<DehydratedClaim>("claim").then((claim) => {
          const subject = getNotificationSubject(
            `${claim.claim.first_name} ${claim.claim.last_name}`,
            "employer response"
          );
          cy.task<Email[]>(
            "getEmails",
            {
              address: "gqzap.notifications@inbox.testmail.app",
              subject,
              timestamp_from: timestamp_from,
            },
            { timeout: 360000 }
          ).then((emails) => {
            expect(emails[0].html).to.contain(fineos_absence_id);
          });
        });
      }
    );
  });
});

