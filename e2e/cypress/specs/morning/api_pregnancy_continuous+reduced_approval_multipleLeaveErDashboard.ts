import { assertValidClaim } from "../../../src/util/typeUtils";
import { fineos, fineosPages, portal } from "../../actions";
import { Submission } from "../../../src/types";
import { addMonths, addDays, format } from "date-fns";
import { extractLeavePeriod } from "../../../src/util/claims";
import { config } from "../../actions/common";

// @note: this test is very similar to api_pregnancy_continuous+reduced_approval+denial_correctExtensionClaimantStatus.ts
// It doesn't include the denial of the extension request as the other test covers this functionality.
// The primary purpose of this test is to test the ER dashboard for claims with multiple absence periods.
// It has been included in the morning group to avoid intermittent failures during deployments. The failure happense when a claimant with a missing FINEOS customer number is used for claim submission.
// More on this issue here: https://nava.slack.com/archives/CTGQMSRLM/p1645651928821799
describe("Submit medical pre-birth application via the web portal", () => {
  it("Submits a Medical/Pregnancy claim through the API", () => {
    cy.task("generateClaim", "PREBIRTH").then((claim) => {
      delete claim.employerResponse;
      cy.task("submitClaimToAPI", claim).then((submission) => {
        cy.stash("claim", claim);
        cy.stash("submission", {
          application_id: submission.application_id,
          fineos_absence_id: submission.fineos_absence_id,
          timestamp_from: Date.now(),
        });
      });
    });
  });

  it("ER will submit an approval for a Medical/Pregnancy claim", () => {
    cy.dependsOnPreviousPass();
    cy.unstash<DehydratedClaim>("claim").then((claim) => {
      cy.unstash<Submission>("submission").then((submission) => {
        assertValidClaim(claim.claim);
        portal.before();
        portal.loginLeaveAdmin(claim.claim.employer_fein);
        portal.goToEmployerDashboard();
        portal.searchClaims(submission.fineos_absence_id, true);
        if (!claim.claim.leave_details?.reason)
          throw Error("Leave reason undefined");
        const leavePeriods = extractLeavePeriod(claim.claim).map((date) =>
          date.toString()
        ) as [string, string];
        portal.leaveAdminAssertClaimStatusFromDashboard([
          {
            leave: claim.claim.leave_details.reason,
            status: "Pending",
            leavePeriods,
            leavePeriodType: "Continuous",
          },
        ]);

        portal.visitActionRequiredERFormPage(
          submission.fineos_absence_id,
          true
        );
        portal.respondToLeaveAdminRequest(false, true, true);
      });
    });
  });

  const approval = it(
    "CSR rep will approve reduced medical application",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass();
      fineos.before();
      cy.unstash<DehydratedClaim>("claim").then((claim) => {
        cy.unstash<Submission>("submission").then((submission) => {
          const claimPage = fineosPages.ClaimPage.visit(
            submission.fineos_absence_id
          );
          claimPage.triggerNotice("Preliminary Designation");
          fineos.onTab("Absence Hub");
          claimPage.adjudicate((adjudication) => {
            adjudication
              .evidence((evidence) => {
                // Receive all of the claim documentation.
                claim.documents.forEach((document) => {
                  evidence.receive(document.document_type);
                });
              })
              .certificationPeriods((cert) => cert.prefill())
              .acceptLeavePlan();
          });
          claimPage.approve("Approved", config("HAS_APRIL_UPGRADE") === "true");
          claimPage.triggerNotice("Designation Notice");
        });
      });
    }
  );
  const extension = it(
    "CSR rep will add bonding leave to the absence case",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass([approval]);
      fineos.before();
      cy.unstash<Submission>("submission").then((submission) => {
        fineosPages.ClaimPage.visit(submission.fineos_absence_id)
          .benefitsExtension((benefitsExtension) => {
            const startDate = addMonths(new Date(), 2);
            const startDateFormatted = format(startDate, "MM/dd/yyyy");
            const endDateFormatted = format(
              addDays(startDate, 2),
              "MM/dd/yyyy"
            );
            cy.stash("extensionDates", [startDateFormatted, endDateFormatted]);
            benefitsExtension.extendLeave(
              startDateFormatted,
              endDateFormatted,
              true,
              "reduced"
            );
          })
          .outstandingRequirements((outstandingRequirements) =>
            outstandingRequirements.add()
          );
      });
    }
  );

  it("Will display the approprite claim statuses for multiple leave requests within a single absence case, while reviewing the second leave request (leave-admin)", () => {
    cy.dependsOnPreviousPass([extension]);
    portal.before();
    cy.unstash<Submission>("submission").then((submission) => {
      cy.unstash<DehydratedClaim>("claim").then((claim) => {
        cy.unstash<[string, string]>("extensionDates").then(
          (extensionDates) => {
            if (!claim.claim.employer_fein)
              throw Error(
                "Property 'employer_fein' undefined in unstashed claim"
              );
            portal.loginLeaveAdmin(claim.claim.employer_fein);
            portal.goToEmployerDashboard();
            portal.searchClaims(submission.fineos_absence_id, true);
            if (!claim.claim.leave_details?.reason)
              throw Error("Leave reason undefined");
            const leavePeriods = extractLeavePeriod(claim.claim).map((date) =>
              date.toString()
            ) as [string, string];
            portal.leaveAdminAssertClaimStatusFromDashboard([
              {
                leave: claim.claim.leave_details.reason,
                status: "Approved",
                leavePeriods,
                leavePeriodType: "Continuous",
              },
              {
                leave: "Child Bonding",
                status: "Pending",
                leavePeriods: extensionDates,
                leavePeriodType: "Reduced",
              },
            ]);
            portal.visitActionRequiredERFormPage(
              submission.fineos_absence_id,
              true
            );
            portal.leaveAdminAssertClaimStatus([
              {
                leave: "Serious Health Condition - Employee",
                status: "Approved",
                leavePeriods,
              },
              {
                leave: "Child Bonding",
                status: "Pending",
                leavePeriods: extensionDates,
              },
            ]);
          }
        );
      });
    });
  });
});
