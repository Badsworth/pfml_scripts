import { fineos, portal, email, fineosPages } from "../../../actions";
import { getFineosBaseUrl, getLeaveAdminCredentials } from "../../../config";
import {
  Submission,
  ApplicationSubmissionResponse,
} from "../../../../src/types";
import { config } from "../../../actions/common";
import {
  findCertificationDoc,
  getDocumentReviewTaskName,
} from "../../../../src/util/documents";

describe("Approval (notifications/notices)", () => {
  after(() => {
    portal.deleteDownloadsFolder();
  });

  const credentials: Credentials = {
    username: config("PORTAL_USERNAME"),
    password: config("PORTAL_PASSWORD"),
  };

  const submit = it(
    "Given a fully approved claim",
    { baseUrl: getFineosBaseUrl() },
    () => {
      fineos.before();
      cy.visit("/");
      // Submit a claim via the API, including Employer Response.
      cy.task("generateClaim", "REDUCED_ER").then((claim) => {
        cy.stash("claim", claim.claim);
        cy.task("submitClaimToAPI", {
          ...claim,
          credentials,
        }).then((response) => {
          cy.stash("submission", {
            application_id: response.application_id,
            fineos_absence_id: response.fineos_absence_id,
            timestamp_from: Date.now(),
          });

          const claimPage = fineosPages.ClaimPage.visit(
            response.fineos_absence_id
          );
          claimPage.adjudicate((adjudication) => {
            adjudication.evidence((evidence) => {
              // Receive and approve all of the documentation for the claim.
              claim.documents.forEach((doc) =>
                evidence.receive(doc.document_type)
              );
            });
            adjudication.certificationPeriods((cert) => cert.prefill());
            adjudication.acceptLeavePlan();
          });
          claimPage.tasks((tasks) => {
            const certificationDoc = findCertificationDoc(claim.documents);
            const certificationTask = getDocumentReviewTaskName(
              certificationDoc.document_type
            );
            tasks.assertTaskExists("ID Review");
            tasks.assertTaskExists(certificationTask);
          });
          claimPage.shouldHaveStatus("Applicability", "Applicable");
          claimPage.shouldHaveStatus("Eligibility", "Met");
          claimPage.shouldHaveStatus("Evidence", "Satisfied");
          claimPage.shouldHaveStatus("Availability", "Time Available");
          claimPage.shouldHaveStatus("Restriction", "Passed");
          claimPage.shouldHaveStatus("PlanDecision", "Accepted");
          claimPage.approve();
          claimPage
            .triggerNotice("Designation Notice")
            .documents((docPage) =>
              docPage.assertDocumentExists("Approval Notice")
            );
        });
      });
    }
  );

  it(
    "Should generate a legal notice (Approval) that the claimant can view",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass([submit]);
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
      cy.dependsOnPreviousPass([submit]);
      portal.before();
      cy.visit("/");
      cy.unstash<Submission>("submission").then((submission) => {
        cy.unstash<ApplicationRequestBody>("claim").then((claim) => {
          if (!claim.employer_fein) {
            throw new Error("Claim must include employer FEIN");
          }
          const employeeFullName = `${claim.first_name} ${claim.last_name}`;
          portal.login(getLeaveAdminCredentials(claim.employer_fein));
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
    "Should generate a 'Action Required' ER notification for the Leave Administrator",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass([submit]);
      cy.unstash<Submission>("submission").then((submission) => {
        cy.unstash<ApplicationRequestBody>("claim").then((claim) => {
          email
            .getEmails(
              {
                address: "gqzap.notifications@inbox.testmail.app",
                subject: `Action required: Respond to ${claim.first_name} ${claim.last_name}'s paid leave application`,
                messageWildcard: submission.fineos_absence_id,
                timestamp_from: submission.timestamp_from,
                debugInfo: {
                  "Fineos Claim ID": submission.fineos_absence_id,
                },
              },
              30000
            )
            .then(() => {
              cy.get(
                `a[href*="/employers/applications/new-application/?absence_id=${submission.fineos_absence_id}"]`
              );
            });
        });
      });
    }
  );

  it(
    "Should generate an approval notification for the Leave Administrator",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass([submit]);
      cy.unstash<Submission>("submission").then((submission) => {
        cy.unstash<ApplicationRequestBody>("claim").then((claim) => {
          const employeeFullName = `${claim.first_name} ${claim.last_name}`;
          const subjectEmployer = email.getNotificationSubject(
            `${claim.first_name} ${claim.last_name}`,
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
                debugInfo: {
                  "Fineos Claim ID": submission.fineos_absence_id,
                },
              },
              // Reduced timeout, since we have multiple tests that run prior to this.
              60000
            )
            .then(() => {
              const dob =
                claim.date_of_birth?.replace(/-/g, "/").slice(5) + "/****";
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
      cy.dependsOnPreviousPass([submit]);
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
              debugInfo: {
                "Fineos Claim ID": submission.fineos_absence_id,
              },
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
