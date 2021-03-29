import { fineos, portal, email } from "../../tests/common/actions";
import { bailIfThisTestFails, beforeFineos } from "../../tests/common/before";
import { beforePortal } from "../../tests/common/before";
import { getFineosBaseUrl, getLeaveAdminCredentials } from "../../config";
import { ApplicationResponse } from "../../../src/api";
import { Submission, LeaveDates } from "../../../src/types";

describe("Post-approval (notifications/notices)", { retries: 0 }, () => {
  it("Create a financially eligible claim in which an employer will respond", () => {
    beforePortal();
    bailIfThisTestFails();

    cy.visit("/");

    // Generate Creds for Registration/Login - submit claim via API
    cy.task("generateCredentials").then((credentials) => {
      cy.stash("credentials", credentials);
      cy.task("registerClaimant", credentials).then(() => {
        cy.task("generateClaim", "MHAP1").then((claim) => {
          if (!claim.claim.leave_details?.continuous_leave_periods) {
            throw new Error ("No leave Period")
          }
          const leave_periods: LeaveDates = {
            start_date: claim.claim.leave_details.continuous_leave_periods[0].start_date as string,
            end_date: claim.claim.leave_details.continuous_leave_periods[0].end_date as string
          }
          cy.stash("claim", claim.claim);
          cy.stash("leave_periods", leave_periods)
          cy.task("submitClaimToAPI", {
            ...claim,
            credentials,
          }).then((response: ApplicationResponse) => {
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
              true,
              leave_periods
            );
          });
        });
      });
    });
  });

  // Check for ER and approval claim in Fineos
  it(
    "In Fineos, complete an Adjudication Approval",
    { baseUrl: getFineosBaseUrl() },
    () => {
      beforeFineos();
      bailIfThisTestFails();


      cy.unstash<Submission>("submission").then((submission) => {
        cy.visit("/");
        fineos.claimAdjudicationFlow(submission.fineos_absence_id, true);  
        const timestamp_fromER = Date.now();
        cy.stash("newTimestamp_from", timestamp_fromER)
        fineos.claimUpdateAfterApprovalFlow(submission.fineos_absence_id);
      });
    }
  );

  it("As an employer, I should receive a notification about my response being required", () => {
    beforePortal();
    cy.unstash<ApplicationRequestBody>("claim").then((claim) => {
      cy.unstash<LeaveDates>("leave_periods").then((leave_periods) => {
        cy.unstash<Submission>("submission").then((submission) => {
          cy.unstash<string>("newTimestamp_from").then((timestamp_fromER) => {
            cy.task<Email[]>(
              "getEmails",
              {
                address: "gqzap.notifications@inbox.testmail.app",
                subject: `Action required: Respond to ${claim.first_name} ${claim.last_name}'s paid leave application`,
                timestamp_from: timestamp_fromER,
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
          })
        })
      })
    })
  })
});
