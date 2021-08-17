import { fineos, fineosPages } from "../../actions";
import { getFineosBaseUrl } from "../../config";
import { Submission, GetClaimFromDBArgs } from "../../../src/types";
import { waitForAjaxComplete } from "../../actions/fineos";
import { ClaimDocument } from "../../claims_database/models/claim";
import { format, parseISO } from "date-fns";

const spec: GetClaimFromDB = {
  filters: { status: "approved" },
  fallbackScenario: "MED_LSDCR",
};

describe("Approval (notifications/notices)", () => {
  const modify = it(
    "Will modify leave dates for an approved claim",
    { baseUrl: getFineosBaseUrl() },
    () => {
      fineos.before();
      cy.visit("/");
      cy.task<ClaimDocument>("getClaimFromDB", spec).then(
        ({ fineosAbsenceId, startDate, endDate }) => {
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
      cy.unstash<Submission>("submission").then((submission) => {
        fineosPages.ClaimPage.visit(submission.fineos_absence_id)
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
