import { fineos, fineosPages, email, portal } from "../../actions";
import { Submission } from "../../../src/types";
import { extractLeavePeriod } from "../../../src/util/claims";
import { addDays, format, subDays } from "date-fns";
import { waitForAjaxComplete } from "../../actions/fineos";
import { getClaimantCredentials } from "../../config";
import { describeIf } from "../../util";
import { config } from "../../actions/common";

describeIf(
  config("HAS_FINEOS_JANUARY_RELEASE") === "true",
  "Approval (notifications/notices)",
  {},
  () => {
    before(() => {
      portal.deleteDownloadsFolder();
    });

    const submission = it("Will submit a medical leave claim", () => {
      cy.task("generateClaim", "MED_LSDCR").then((claim) => {
        cy.stash("claim", claim);
        cy.task("submitClaimToAPI", claim).then((response) => {
          if (!response.fineos_absence_id) {
            throw new Error("Response contained no fineos_absence_id property");
          }
          const submission: Submission = {
            application_id: response.application_id,
            fineos_absence_id: response.fineos_absence_id,
            timestamp_from: Date.now(),
          };
          cy.stash("submission", submission);
        });
      });
    });
    const approval = it("CSR rep will approve a medical leave", () => {
      cy.dependsOnPreviousPass([submission]);
      fineos.before();
      // Submit a claim via the API, including Employer Response.
      cy.unstash<Submission>("submission").then((submission) => {
        cy.unstash<DehydratedClaim>("claim").then((claim) => {
          const [startDate, endDate] = extractLeavePeriod(claim.claim);
          const newStartDate = format(
            addDays(new Date(startDate), 5),
            "MM/dd/yyyy"
          );
          const newEndDate = format(subDays(new Date(endDate), 5), "MM/dd/yyyy");
          cy.stash("modifiedDates", [newStartDate, newEndDate]);
          // approve claim
          fineosPages.ClaimPage.visit(submission.fineos_absence_id)
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
            .approve();
        });
      });
    });
    const modify = it("Will modify leave dates for an approved claim", () => {
      cy.dependsOnPreviousPass([submission, approval]);
      fineos.before();
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
              });
          }
        );
      });
    });
    const changeNotice =
      it('Generates and adds a "Change Leave Request Approved" document', () => {
        cy.dependsOnPreviousPass([submission, approval, modify]);
        fineos.before();
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
            // Trigger the Approval notice first before the next notice.
            .triggerNotice("Designation Notice")
            .documents((docPage) =>
              docPage.assertDocumentExists("Approval Notice")
            )
            .adjudicate((ad) => {
              waitForAjaxComplete();
              ad.acceptLeavePlan();
            })
            .outstandingRequirements((outstandingRequirement) =>
              outstandingRequirement.complete(
                "Received",
                "Complete Employer Confirmation",
                true
              )
            )
            .approve()
            .triggerNotice("Review Approval Notice")
            .documents((docPage) =>
              docPage.assertDocumentExists("Change Request Approved")
            );
        });
      });
    it(
      "Check the Claimant email for the Change Request Approved notification",
      { retries: 0 },
      () => {
        {
          cy.dependsOnPreviousPass([submission, approval, modify, changeNotice]);
          cy.unstash<Submission>("submission").then((submission) => {
            cy.unstash<ApplicationRequestBody>("claim").then((claim) => {
              // The notification is using the same subject line as Appeals claimant.
              const subjectClaimant = email.getNotificationSubject(
                "appeal (claimant)",
                submission.fineos_absence_id,
                `${claim.first_name} ${claim.last_name}`
              );
              email
                .getEmails(
                  {
                    address: "gqzap.notifications@inbox.testmail.app",
                    subject: subjectClaimant,
                    messageWildcard: {
                      pattern: `${submission.fineos_absence_id}.*Your change request has been approved`
                    },
                    timestamp_from: submission.timestamp_from,
                    debugInfo: { "Fineos Claim ID": submission.fineos_absence_id },
                  },
                  60000
                )
                .then(() => {
                  cy.screenshot("Claimant email");
                  cy.get(`a[href$="/applications/status/?absence_case_id=${submission.fineos_absence_id}#view-notices"]`);
                });
            });
          });
        }
      }
    );
    it(
      "Check the Leave Admin email for the Change Request Approved notification",
      { retries: 0 },
      () => {
        cy.dependsOnPreviousPass([submission, approval, modify, changeNotice]);
        cy.unstash<Submission>("submission").then((submission) => {
          cy.unstash<ApplicationRequestBody>("claim").then((claim) => {
            // The notification is using the same subject line as Appeals claimant.
            const subjectEmployer = email.getNotificationSubject(
              "appeal (claimant)",
              submission.fineos_absence_id,
              `${claim.first_name} ${claim.last_name}`
            );
            email
              .getEmails(
                {
                  address: "gqzap.notifications@inbox.testmail.app",
                  subject: subjectEmployer,
                  messageWildcard: {
                    pattern: `${submission.fineos_absence_id}.*The applicant’s change request has been approved`
                  },
                  timestamp_from: submission.timestamp_from,
                  debugInfo: { "Fineos Claim ID": submission.fineos_absence_id },
                },
                60000
              )
              .then(() => {
                cy.screenshot("Leave Admin email");
                cy.get(`a[href*="/employers/applications/status/?absence_id=${submission.fineos_absence_id}"]`);
              });
          });
        });
      }
    );
    it(
      "Check the Leave Admin Portal for the Change Request Approved notice",
      { retries: 0 },
      () => {
        cy.dependsOnPreviousPass([submission, approval, modify, changeNotice]);
        portal.before();
        cy.unstash<Submission>("submission").then((submission) => {
          cy.unstash<DehydratedClaim>("claim").then((claim) => {
            if (!claim.claim.employer_fein) {
              throw new Error("Claim must include employer FEIN");
            }
            const employeeFullName = `${claim.claim.first_name} ${claim.claim.last_name}`;
            portal.loginLeaveAdmin(claim.claim.employer_fein);
            portal.selectClaimFromEmployerDashboard(submission.fineos_absence_id);
            portal.checkNoticeForLeaveAdmin(
              submission.fineos_absence_id,
              employeeFullName,
              "Change Request Approved (PDF)"
            );
            portal.downloadLegalNotice(submission.fineos_absence_id);
          });
        });
      }
    );
    it(
      "Check the Claimant Portal for the legal notice (Change Request Approved)",
      { retries: 0 },
      () => {
        cy.dependsOnPreviousPass([submission, approval, modify, changeNotice]);
        portal.before();
        cy.unstash<Submission>("submission").then((submission) => {
          portal.loginClaimant();
          cy.log("Waiting for documents");
          cy.task(
            "waitForClaimDocuments",
            {
              credentials: getClaimantCredentials(),
              application_id: submission.application_id,
              document_type: "Change Request Approved",
            },
            { timeout: 45000 }
          );
          cy.log("Finished waiting for documents");
          portal.claimantGoToClaimStatus(submission.fineos_absence_id);
          portal.claimantAssertClaimStatus([
            {
              leave: "Serious Health Condition - Employee",
              status: "Approved",
            },
          ]);
          cy.findByText("Change Request Approved (PDF)")
            .should("be.visible")
            .click({ force: true });
          portal.downloadLegalNotice(submission.fineos_absence_id);
        });
      }
    );
    // Checking a secure action is available in FINEOS where certain users are
    // able to change or edit the document.
    it("Check to see if a document can be changed in the Documents tab", () => {
      cy.dependsOnPreviousPass([submission, approval, modify]);
      fineos.before();
      cy.unstash<Submission>("submission").then((submission) => {
        fineosPages.ClaimPage.visit(submission.fineos_absence_id).documents(
          (docPage) => {
            docPage.changeDocType(
              "Identification Proof",
              "State managed Paid Leave Confirmation",
              true
            );
          }
        );
      });
    });
  }
);
