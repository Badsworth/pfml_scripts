import { fineos, fineosPages, portal, email } from "../../../actions";
import { getFineosBaseUrl, getLeaveAdminCredentials } from "../../../config";
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
  const submission = it("Will submit a medical leave claim", () => {
    cy.task("generateClaim", "BHAP1_RED_LSDCR").then((claim) => {
      cy.stash("claim", claim);
      cy.task("submitClaimToAPI", {
        ...claim,
        credentials,
      }).then((response) => {
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
  const approval = it(
    "CSR rep will approve a medical leave",
    { baseUrl: getFineosBaseUrl() },
    () => {
      cy.dependsOnPreviousPass([submission]);
      fineos.before();
      cy.visit("/");
      // Submit a claim via the API, including Employer Response.
      cy.unstash<Submission>("submission").then((submission) => {
        cy.unstash<DehydratedClaim>("claim").then((claim) => {
          const [startDate, endDate] = extractLeavePeriod(
            claim.claim,
            "reduced_schedule_leave_periods"
          );
          const newStartDate = format(
            addDays(new Date(startDate), 5),
            "MM/dd/yyyy"
          );
          const newEndDate = format(
            subDays(new Date(endDate), 5),
            "MM/dd/yyyy"
          );
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
                .close("Bonding Certification Review")
                .close("ID Review")
                .close("Employer Approval Received");
            })
            .shouldHaveStatus("Applicability", "Applicable")
            .shouldHaveStatus("Eligibility", "Met")
            .shouldHaveStatus("Evidence", "Satisfied")
            .shouldHaveStatus("Availability", "Time Available")
            .shouldHaveStatus("Restriction", "Passed")
            .shouldHaveStatus("PlanDecision", "Accepted")
            .approve()
            .triggerNotice("Designation Notice")
            .documents((docPage) =>
              docPage.assertDocumentExists("Approval Notice")
            );
        });
      });
    }
  );
  const modify = it(
    "Will modify leave dates for an approved claim",
    { baseUrl: getFineosBaseUrl() },
    () => {
      cy.dependsOnPreviousPass([submission, approval]);
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
                    requestInformation.editRequestDates(
                      "2021-06-02",
                      "2021-06-05"
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
      });
    }
  );
  it(
    'Generates and adds a "Change Leave Request Approved" document',
    { baseUrl: getFineosBaseUrl() },
    () => {
      cy.dependsOnPreviousPass([submission, approval, modify]);
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
  it(
    "Should generate a legal notice (Approval) that the claimant can view",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass([approval]);
      portal.before();
      cy.visit("/");
      portal.login(credentials);
      cy.unstash<Submission>("submission").then((submission) => {
        // Wait for the legal document to arrive.
        cy.task(
          "waitForClaimDocuments",
          {
            credentials: credentials,
            application_id: submission.application_id,
            document_type: "Approval Notice",
          },
          { timeout: 30000 }
        );
        cy.visit("/applications");
        cy.contains("article", submission.fineos_absence_id).within(() => {
          cy.findByText("Approval notice (PDF)").should("be.visible").click();
        });
        portal.downloadLegalNotice(submission.fineos_absence_id);
      });
    }
  );
  it(
    "Should generate a legal notice (Approval) that the Leave Administrator can view",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass([approval]);
      portal.before();
      cy.visit("/");
      cy.unstash<Submission>("submission").then((submission) => {
        cy.unstash<DehydratedClaim>("claim").then((claim) => {
          if (!claim.claim.employer_fein) {
            throw new Error("Claim must include employer FEIN");
          }
          const employeeFullName = `${claim.claim.first_name} ${claim.claim.last_name}`;
          portal.login(getLeaveAdminCredentials(claim.claim.employer_fein));
          portal.selectClaimFromEmployerDashboard(
            submission.fineos_absence_id,
            "--"
          );
          portal.checkNoticeForLeaveAdmin(
            submission.fineos_absence_id,
            employeeFullName,
            "approval"
          );
          portal.downloadLegalNotice(submission.fineos_absence_id);
        });
      });
    }
  );
  it(
    "Should generate an approval notification for the Leave Administrator",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass([approval]);
      cy.unstash<Submission>("submission").then((submission) => {
        cy.unstash<DehydratedClaim>("claim").then((claim) => {
          const employeeFullName = `${claim.claim.first_name} ${claim.claim.last_name}`;
          const subjectEmployer = email.getNotificationSubject(
            `${claim.claim.first_name} ${claim.claim.last_name}`,
            "approval (employer)",
            submission.fineos_absence_id
          );
          // Check email for Employer/Leave Admin
          email
            .getEmails(
              {
                address: "gqzap.notifications@inbox.testmail.app",
                subject: subjectEmployer,
                messageWildcard: submission.fineos_absence_id,
                timestamp_from: submission.timestamp_from,
                debugInfo: { "Fineos Claim ID": submission.fineos_absence_id },
              },
              // Reduced timeout, since we have multiple tests that run prior to this.
              30000
            )
            .then(() => {
              const dob =
                claim.claim.date_of_birth?.replace(/-/g, "/").slice(5) +
                "/****";
              cy.log("DOB", dob);
              cy.contains(dob);
              cy.contains(employeeFullName);
              cy.contains(submission.fineos_absence_id);
              cy.get(
                `a[href*="/employers/applications/status/?absence_id=${submission.fineos_absence_id}"]`
              );
            });
        });
      });
    }
  );
  it(
    "Should generate an approval notification for the claimant",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass([approval]);
      cy.unstash<Submission>("submission").then((submission) => {
        cy.unstash<ApplicationRequestBody>("claim").then((claim) => {
          const subjectClaimant = email.getNotificationSubject(
            `${claim.first_name} ${claim.last_name}`,
            "approval (claimant)",
            submission.fineos_absence_id
          );
          // Check email for Claimant/Employee
          email.getEmails(
            {
              address: "gqzap.notifications@inbox.testmail.app",
              subject: subjectClaimant,
              messageWildcard: submission.fineos_absence_id,
              timestamp_from: submission.timestamp_from,
              debugInfo: { "Fineos Claim ID": submission.fineos_absence_id },
            },
            // Reduced timeout, since we have multiple tests that run prior to this.
            30000
          );
          cy.contains(submission.fineos_absence_id);
          cy.get(`a[href*="${config("PORTAL_BASEURL")}/applications"]`);
        });
      });
    }
  );
});
