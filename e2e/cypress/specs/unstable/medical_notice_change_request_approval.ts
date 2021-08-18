import { fineos, fineosPages } from "../../actions";
import { getFineosBaseUrl } from "../../config";
import { Submission, GetClaimFromDBArgs } from "../../../src/types";
import { waitForAjaxComplete } from "../../actions/fineos";
import { ClaimDocument } from "../../claims_database/models/claim";
import { format, parseISO } from "date-fns";
import { config } from "../../actions/common";
import * as scenarios from "../../../src/scenarios";
import { getCertificationDocumentType } from "util/documents";

const spec: GetClaimFromDBArgs = {
  filters: { status: "approved", environment: config("ENVIRONMENT") },
  fallbackScenario: "MED_LSDCR",
};

describe("Approval (notifications/notices)", () => {
  // @todo: what's the best approach to handle scenario where no claim meets the spec => freshly submitted claim is adjudication
  // const approval = it("Approves a claim", () => {
  //   cy.task<ClaimDocument>("getClaimFromDB", spec).then((claim) => {
  //     cy.stash("claim", claim);
  //     if (claim.status === "approved") return;
  //     const claimPage = fineosPages.ClaimPage.visit(claim.fineosAbsenceId);
  //     claimPage.adjudicate((adjudication) => {
  //       adjudication.evidence((evidence) => {
  //         // Receive all of the claim documentation.
  //         scenarios[claim.scenario].claim; //@todo mark evidence, would either have to save document types in db or return generated claim from this task
  //       });
  //       adjudication.certificationPeriods((cert) => cert.prefill());
  //       adjudication.acceptLeavePlan();
  //     });
  //     claimPage.shouldHaveStatus("Applicability", "Applicable");
  //     claimPage.shouldHaveStatus("Eligibility", "Met");
  //     claimPage.shouldHaveStatus("Evidence", "Satisfied");
  //     claimPage.shouldHaveStatus("Availability", "Time Available");
  //     claimPage.shouldHaveStatus("Restriction", "Passed");
  //     claimPage.shouldHaveStatus("PlanDecision", "Accepted");
  //     claimPage.approve();
  //   });
  // });

  const modify = it(
    "Will modify leave dates for an approved claim",
    { baseUrl: getFineosBaseUrl() },
    () => {
      fineos.before();
      cy.visit("/");
      cy.task<ClaimDocument>("getClaimFromDB", spec).then(
        ({ fineosAbsenceId, startDate, endDate }) => {
          cy.stash("fineosAbsenceId", fineosAbsenceId);
          // visit claim after approval for start date change request w approval
          fineosPages.ClaimPage.visit(fineosAbsenceId)
            .tasks((task) => {
              task
                .add("Approved Leave Start Date Change")
                .editActivityDescription(
                  "Approved Leave Start Date Change",
                  `Leave will now start ${startDate} and end ${endDate}`
                );
            })
            .leaveDetails((leaveDetails) => {
              const adjudication = leaveDetails.editLeavePostApproval();
              adjudication.editPlanDecision("Undecided");
              adjudication
                .availability((page) => {
                  page.reevaluateAvailability("Denied", "Proof");
                })
                .certificationPeriods((certificationPeriods) => {
                  certificationPeriods.remove();
                })
                .requestInformation((requestInformation) => {
                  requestInformation.editRequestDates(
                    format(parseISO(startDate), "MM/dd/yyyy"),
                    format(parseISO(endDate), "MM/dd/yyyy")
                  );
                })
                .certificationPeriods((certificationPeriods) => {
                  certificationPeriods.prefill();
                });
              cy.get("#footerButtonsBar").within(() => {
                cy.findByText("OK").click({ force: true });
              });
            });
        }
      );
    }
  );
  it(
    'Generates and adds a "Change Leave Request Approved" document',
    { baseUrl: getFineosBaseUrl() },
    () => {
      cy.dependsOnPreviousPass([modify]);
      fineos.before();
      cy.visit("/");
      cy.unstash<string>("fineosAbsenceId").then((fineosAbsenceId) => {
        fineosPages.ClaimPage.visit(fineosAbsenceId)
          .outstandingRequirements((outstandingRequirement) => {
            outstandingRequirement.add();
          })
          .tasks((tasks) => {
            tasks.close("Approved Leave Start Date Change");
            tasks.add("Update Paid Leave Case");
            tasks.assertIsAssignedToDepartment(
              "Update Paid Leave Case",
              "DFML Program Integrity"
            );
          })
          .triggerNotice("Designation Notice")
          .documents((docPage) =>
            docPage.assertDocumentExists("Approval Notice")
          )
          .adjudicate((ad) => {
            waitForAjaxComplete();
            ad.acceptLeavePlan();
          })
          .outstandingRequirements((outstandingRequirement) =>
            outstandingRequirement.complete()
          )
          .approve()
          .triggerNotice("Review Approval Notice")
          .documents((docPage) =>
            docPage.assertDocumentExists("Change Request Approved")
          );
      });
    }
  );
});
