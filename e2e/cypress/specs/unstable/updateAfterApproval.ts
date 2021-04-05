import { fineos, portal } from "../../tests/common/actions";
import { bailIfThisTestFails, beforeFineos } from "../../tests/common/before";
import { beforePortal } from "../../tests/common/before";
import { getFineosBaseUrl, getLeaveAdminCredentials } from "../../config";
import { ApplicationResponse } from "../../../src/api";
import { Submission, LeaveDates } from "../../../src/types";
import { extractLeavePeriod } from "../../../cypress/utils";

describe("Post-approval (notifications/notices)", { retries: 0 }, () => {
  it("Create a financially eligible claim in which an employer will respond", () => {
    beforePortal();
    bailIfThisTestFails();

    cy.visit("/");

    // Generate Creds for Registration/Login - submit claim via API
    cy.task("generateClaim", "MHAP1").then((claim) => {
      if (!claim.claim.leave_details?.continuous_leave_periods) {
        throw new Error("No leave Period");
      }
      // const [startDate, endDate] = extractLeavePeriod(claim.claim);
      // const leave_periods: LeaveDates = {
      //   start_date: startDate,
      //   end_date: endDate
      // }
      cy.stash("claim", claim.claim);
      cy.task<ApplicationResponse>("submitClaimToAPI", claim).then(
        (response) => {
          console.log(response);
          const timestamp_fromER = Date.now();
          cy.stash("submission", {
            application_id: response.application_id,
            fineos_absence_id: response.fineos_absence_id,
            timestamp_from: Date.now(),
          });
          // Complete Employer Response
          if (typeof claim.claim.employer_fein !== "string") {
            throw new Error("Claim must include employer FEIN");
          }
          if (typeof response.fineos_absence_id !== "string") {
            throw new Error("Response must include FINEOS absence ID");
          }

          // As an employer, I should receive a notification about my response being required
          cy.task<Email[]>(
            "getEmails",
            {
              address: "gqzap.notifications@inbox.testmail.app",
              subject: `Action required: Respond to ${claim.claim.first_name} ${claim.claim.last_name}'s paid leave application`,
              timestamp_from: timestamp_fromER,
              debugInfo: { "Fineos Claim ID": response.fineos_absence_id },
            },
            { timeout: 360000 }
          ).then((emails) => {
            expect(emails.length).to.be.greaterThan(0);
            expect(emails[0].html).to.contain(
              `/employers/applications/new-application/?absence_id=${response.fineos_absence_id}`
            );
          });

          // Access and fill out ER form
          portal.login(getLeaveAdminCredentials(claim.claim.employer_fein));
          portal.respondToLeaveAdminRequest(
            response.fineos_absence_id,
            false,
            true,
            true
          );
        }
      );
    });
    // });
  });

  // Adudicaiton and Post Approval Flow
  it(
    "In Fineos, complete an Adjudication Approval along w/Post Approval Flow",
    { baseUrl: getFineosBaseUrl() },
    () => {
      beforeFineos();
      bailIfThisTestFails();
      cy.visit("/");

      cy.unstash<Submission>("submission").then((submission) => {
        cy.task("approveFineosClaim", submission.fineos_absence_id);
        cy.visit("/");
        fineos.visitClaim(submission.fineos_absence_id, true);
        cy.stash("newTimestamp_from", Date.now());
        fineos.claimUpdateAfterApprovalFlow(submission.fineos_absence_id);
      });
    }
  );

  // Check for new RFI ER form
  it("As an employer, I should receive a second notification (RFI w/updated dates) about my response being required", () => {
    beforePortal();
    cy.unstash<Date>("newTimestamp_from").then((newTimestamp_from) => {
      cy.unstash<Submission>("submission").then((submission) => {
        cy.unstash<ApplicationRequestBody>("claim").then((claim) => {
          console.log("date", newTimestamp_from);
          // cy.wait(3000)

          const [startDate, endDate] = extractLeavePeriod(claim);
          const leave_periods: LeaveDates = {
            start_date: startDate,
            end_date: endDate,
          };
          cy.task<Email[]>(
            "getEmails",
            {
              address: "gqzap.notifications@inbox.testmail.app",
              subject: `Action required: Respond to ${claim.first_name} ${claim.last_name}'s paid leave application`,
              timestamp_from: newTimestamp_from,
            },
            { timeout: 360000 }
          ).then((emails) => {
            expect(emails.length).to.be.greaterThan(0);
            expect(emails[0].html).to.contain(
              `/employers/applications/new-application/?absence_id=${submission.fineos_absence_id}`
            );
          });

          portal.login(getLeaveAdminCredentials(claim.employer_fein as string));
          portal.respondToLeaveAdminRequest(
            submission.fineos_absence_id,
            false,
            true,
            true,
            leave_periods
          );
        });
      });
    });
  });
});
