import { fineos, portal, fineosPages } from "../../../actions";
import { Submission } from "../../../../src/types";
import { extractLeavePeriod } from "../../../../src/util/claims";
import { assertValidClaim } from "../../../../src/util/typeUtils";
import { format, addDays } from "date-fns";
import { config } from "../../../actions/common";

describe("Claim date change", () => {
  after(() => {
    portal.deleteDownloadsFolder();
  });
  const submit = it("Given a fully approved claim", () => {
    fineos.before();
    // Submit a claim via the API, including Employer Response.
    cy.task("generateClaim", "BHAP1ER").then((claim) => {
      cy.stash("claim", claim);
      cy.task("submitClaimToAPI", claim).then((res) => {
        const [startDate, endDate] = extractLeavePeriod(claim.claim);
        cy.stash("submission", {
          application_id: res.application_id,
          fineos_absence_id: res.fineos_absence_id,
          timestamp_from: Date.now(),
        });
        const newStartDate = format(
          addDays(new Date(startDate), 1),
          "MM/dd/yyyy"
        );
        const newEndDate = format(addDays(new Date(endDate), 8), "MM/dd/yyyy");
        cy.stash("changedLeaveDates", [newStartDate, newEndDate]);
        const claimPage = fineosPages.ClaimPage.visit(res.fineos_absence_id);
        claimPage.adjudicate((adjudication) => {
          adjudication.evidence((evidence) => {
            for (const document of claim.documents) {
              evidence.receive(document.document_type);
            }
          });
          cy.wait("@ajaxRender");
          cy.wait(200);
          adjudication.certificationPeriods((certificationPeriods) =>
            certificationPeriods.prefill()
          );
          adjudication.acceptLeavePlan();
        });
        claimPage.tasks((task) => {
          task.close("Bonding Certification Review");
          task.close("ID Review");
        });
        claimPage.approve("Approved", config("HAS_APRIL_UPGRADE") === "true");
      });
    });
  });

  const dateChange = it("CSR rep can update the leave dates", () => {
    cy.dependsOnPreviousPass([submit]);
    cy.unstash<DehydratedClaim>("claim").then((_claim) => {
      cy.unstash<Submission>("submission").then(({ fineos_absence_id }) => {
        cy.unstash<[string, string]>("changedLeaveDates").then(
          ([startDate, endDate]) => {
            fineos.before();
            const claimPage = fineosPages.ClaimPage.visit(fineos_absence_id);
            claimPage.tasks((task) => {
              task.add("Approved Leave Start Date Change");
              task.editActivityDescription(
                "Approved Leave Start Date Change",
                `Date change request: Move to ${startDate} - ${endDate}`,
                config("HAS_APRIL_UPGRADE") === "true" ? true : false
              );
            });
            if (config("HAS_APRIL_UPGRADE") === "true") {
              claimPage.reviewClaim(true);
              claimPage.adjudicateUpgrade((adjudication) => {
                // These steps might need to be updated after FINEOS demo (3/10/22) of the changes from in Review
                // process going on in the background. SOP might be updated if so this will need to be updated.
                adjudication.certificationPeriods((certificationPeriods) =>
                  certificationPeriods.remove()
                );
                adjudication.requestInformation((requestInformation) =>
                  requestInformation.editRequestDates(startDate, endDate)
                );
                adjudication.certificationPeriods((certificationPeriods) =>
                  certificationPeriods.prefill()
                );
              });
              claimPage.shouldHaveStatus("PlanDecision", "Undecided");
              claimPage.outstandingRequirements((outstandingRequirements) => {
                outstandingRequirements.add();
              });
              claimPage.tasks((task) => {
                task.close("Approved Leave Start Date Change");
                task.add("Update Paid Leave Case");
              });
            } else {
              claimPage.reviewClaim(false);
              const claimReviewed =
                fineosPages.ClaimPage.visit(fineos_absence_id);
              claimReviewed.adjudicate((adjudication) => {
                adjudication.editPlanDecision("Undecided");
                adjudication.certificationPeriods((certificationPeriods) =>
                  certificationPeriods.remove()
                );
                adjudication.requestInformation((requestInformation) =>
                  requestInformation.editRequestDates(startDate, endDate)
                );
                adjudication.certificationPeriods((certificationPeriods) =>
                  certificationPeriods.prefill()
                );
              });
              claimReviewed.shouldHaveStatus("PlanDecision", "Undecided");
              claimReviewed.outstandingRequirements(
                (outstandingRequirements) => {
                  outstandingRequirements.add();
                }
              );
              claimReviewed.tasks((task) => {
                task.close("Approved Leave Start Date Change");
                task.add("Update Paid Leave Case");
              });
            }
          }
        );
      });
    });
  });

  it("Should show the changed dates in Portal.", { retries: 0 }, () => {
    cy.dependsOnPreviousPass([submit, dateChange]);
    portal.before();
    cy.unstash<DehydratedClaim>("claim").then(({ claim }) => {
      cy.unstash<Submission>("submission").then(({ fineos_absence_id }) => {
        cy.unstash<string[]>("changedLeaveDates").then(([start, end]) => {
          assertValidClaim(claim);
          portal.loginLeaveAdmin(claim.employer_fein);
          portal.selectClaimFromEmployerDashboard(fineos_absence_id);
          cy.url().should("not.include", "dashboard");
          cy.contains(`${claim.first_name} ${claim.last_name}`);
          if (!claim.leave_details.reason)
            throw TypeError("Claim missing leave reason");
          portal.leaveAdminAssertClaimStatus([
            {
              leave: claim.leave_details.reason,
              status: "Pending",
              leavePeriods: [start, end],
            },
          ]);
          portal.respondToLeaveAdminRequest(false, true, true);
        });
      });
    });
  });
});
