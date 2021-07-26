import { fineos, fineosPages } from "../../../actions";
import { getFineosBaseUrl } from "../../../config";
import { Submission } from "../../../../src/types";
import { config } from "../../../actions/common";
import { extractLeavePeriod } from "../../../../src/util/claims";
import { addDays, format, subDays } from "date-fns";
import { waitForAjaxComplete } from "../../../actions/fineos";

describe("Approval (notifications/notices)", () => {
  const credentials: Credentials = {
    username: config("PORTAL_USERNAME"),
    password: config("PORTAL_PASSWORD"),
  };

  it(
    "Will submit and approve a medical leave",
    { baseUrl: getFineosBaseUrl() },
    () => {
      fineos.before();
      cy.visit("/");
      // Submit a claim via the API, including Employer Response.
      cy.task("generateClaim", "MED_LSDCR").then((claim) => {
        cy.stash("claim", claim.claim);
        cy.task("submitClaimToAPI", {
          ...claim,
          credentials,
        }).then((response) => {
          if (!response.fineos_absence_id) {
            throw new Error("Response contained no fineos_absence_id property");
          }
          const [startDate, endDate] = extractLeavePeriod(claim.claim);
          const newStartDate = format(
            addDays(new Date(startDate), 5),
            "MM/dd/yyyy"
          );
          const newEndDate = format(
            subDays(new Date(endDate), 5),
            "MM/dd/yyyy"
          );
          const submission: Submission = {
            application_id: response.application_id,
            fineos_absence_id: response.fineos_absence_id,
            timestamp_from: Date.now(),
          };

          cy.stash("modifiedDates", [newStartDate, newEndDate]);
          cy.stash("submission", submission);
          // approve claim
          fineosPages.ClaimPage.visit(response.fineos_absence_id)
            .adjudicate((adjudication) => {
              adjudication
                .evidence((evidence) => {
                  claim.documents.forEach((doc) =>
                    evidence.receive(doc.document_type)
                  );
                })
                .certificationPeriods((cert) => cert.prefill())
                .acceptLeavePlan();
            })
            .tasks((task) => {
              task
                .close("Medical Certification Review")
                .close("ID Review")
                .close("Employer Approval Received");
            })
            .shouldHaveStatus("Applicability", "Applicable")
            .shouldHaveStatus("Eligibility", "Met")
            .shouldHaveStatus("Evidence", "Satisfied")
            .shouldHaveStatus("Availability", "Time Available")
            .shouldHaveStatus("Restriction", "Passed")
            .shouldHaveStatus("PlanDecision", "Accepted")
            .approve();
        });
      });
    }
  );

  it(
    'Generates and adds a "Change Leave Request Approved" document',
    { baseUrl: getFineosBaseUrl() },
    () => {
      fineos.before();
      cy.visit("/");

      cy.unstash<Submission>("submission").then((submission) => {
        cy.unstash<[string, string]>("modifiedDates").then(
          ([startDate, endDate]) => {
            // visit claim after approval for start date change request w approval
            fineosPages.ClaimPage.visit(submission.fineos_absence_id)
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
                    requestInformation.editRequestDates(startDate, endDate);
                  })
                  .certificationPeriods((certificationPeriods) => {
                    certificationPeriods.prefill();
                  });
                cy.get("#footerButtonsBar").within(() => {
                  cy.findByText("OK").click({ force: true });
                });
              })
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
          }
        );
      });
    }
  );
});
