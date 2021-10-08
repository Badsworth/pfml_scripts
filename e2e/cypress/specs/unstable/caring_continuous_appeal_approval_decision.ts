import { portal, fineos, email, fineosPages } from "../../actions";
import {
  getClaimantCredentials,
  getFineosBaseUrl,
  getLeaveAdminCredentials,
} from "../../config";
import { assertValidClaim } from "../../../src/util/typeUtils";
import { Submission } from "../../../src/types";

describe("Submit a claim through Portal: Verify it creates an absence case in Fineos", () => {
  after(() => {
    portal.deleteDownloadsFolder();
  });
  const fineosSubmission =
    it("As a claimant, I should be able to submit a claim application through the portal", () => {
      portal.before();
      cy.task("generateClaim", "CDENY2").then((claim) => {
        cy.stash("claim", claim);
        const application: ApplicationRequestBody = claim.claim;
        const paymentPreference = claim.paymentPreference;
        portal.loginClaimant();
        portal.goToDashboardFromApplicationsPage();

        // Submit Claim
        portal.startClaim();
        portal.submitClaimPartOne(application);
        portal.waitForClaimSubmission().then((data) => {
          cy.stash("submission", {
            application_id: data.application_id,
            fineos_absence_id: data.fineos_absence_id,
            timestamp_from: Date.now(),
          });
        });
        portal.submitClaimPartsTwoThree(application, paymentPreference);
      });
    });

  const employerApproval =
    it("Leave admin will submit ER approval for employee", () => {
      cy.dependsOnPreviousPass([fineosSubmission]);
      portal.before();
      cy.unstash<DehydratedClaim>("claim").then((claim) => {
        cy.unstash<Submission>("submission").then(({ fineos_absence_id }) => {
          assertValidClaim(claim.claim);
          portal.login(getLeaveAdminCredentials(claim.claim.employer_fein));
          portal.selectClaimFromEmployerDashboard(fineos_absence_id);
          portal.visitActionRequiredERFormPage(fineos_absence_id);
          portal.respondToLeaveAdminRequest(false, true, true, true);
        });
      });
    });

  it("CSR will approve a claim", { baseUrl: getFineosBaseUrl() }, () => {
    cy.dependsOnPreviousPass([fineosSubmission, employerApproval]);
    fineos.before();
    cy.unstash<DehydratedClaim>("claim").then((claim) => {
      cy.unstash<Submission>("submission").then((submission) => {
        const claimPage = fineosPages.ClaimPage.visit(
          submission.fineos_absence_id
        );
        claimPage.adjudicate((adjudicate) => {
          adjudicate.evidence((evidence) => {
            claim.documents.forEach((document) => {
              evidence.receive(document.document_type);
            });
          });
          adjudicate.certificationPeriods((cert) => cert.prefill());
          adjudicate.acceptLeavePlan();
        });
        claimPage.approve();
      });
    });
  });

  it(
    "CSR will process the appeal for schedule hearing",
    { baseUrl: getFineosBaseUrl() },
    () => {
      cy.dependsOnPreviousPass([fineosSubmission, employerApproval]);
      fineos.before();
      cy.visit("/");
      cy.unstash<Submission>("submission").then(({ fineos_absence_id }) => {
        const claimPage = fineosPages.ClaimPage.visit(fineos_absence_id);
        claimPage.addAppeal();
        claimPage.triggerNotice("SOM Generate Appeals Notice");
        claimPage.appealDocuments((docPage) => {
          docPage.assertDocumentExists("Appeal Acknowledgment");
        });
        claimPage.appealTasks((tasks) => {
          tasks.closeAppealReview();
          tasks.close("Schedule Hearing");
          tasks.close("Conduct Hearing");
          tasks.closeConductHearing();
          tasks.assertTaskExists("Send Decision Notice");
        });
        claimPage.appealDocuments((docPage) => {
          docPage.uploadDocument("Appeal Notice - Claim Decision Changed");
          docPage.assertDocumentUploads(
            "Appeal Notice - Claim Decision Changed"
          );
        });
      });
    }
  );
  it(
    "Check the Claimant email for the appeal notification.",
    { retries: 0 },
    () => {{
      cy.dependsOnPreviousPass([fineosSubmission, employerApproval]);
      cy.unstash<Submission>("submission").then((submission) => {
        cy.unstash<ApplicationRequestBody>("claim").then((claim) => {
          const subjectClaimant = email.getNotificationSubject(
            "appeal (claimant)",
            submission.fineos_absence_id,
            `${claim.first_name} ${claim.last_name}`
          );
          email.getEmails(
            {
              address: "gqzap.notifications@inbox.testmail.app",
              subject: subjectClaimant,
              messageWildcard: submission.fineos_absence_id,
              timestamp_from: submission.timestamp_from,
              debugInfo: { "Fineos Claim ID": submission.fineos_absence_id },
            },
            30000
          );
          cy.contains(submission.fineos_absence_id);
        });
      });
    }
  });
  it(
    "Check the Leave Admin email for the appeal notification.",
    { retries: 0 },
    () => {
      portal.before();
      cy.dependsOnPreviousPass([fineosSubmission, employerApproval]);
      cy.unstash<Submission>("submission").then((submission) => {
        cy.unstash<ApplicationRequestBody>("claim").then((claim) => {
          const subjectEmployer = email.getNotificationSubject(
            "appeal (employer)",
            submission.fineos_absence_id,
            `${claim.first_name} ${claim.last_name}`
          );
          email
            .getEmails(
              {
                address: "gqzap.notifications@inbox.testmail.app",
                subject: subjectEmployer,
                messageWildcard: submission.fineos_absence_id,
                timestamp_from: submission.timestamp_from,
                debugInfo: { "Fineos Claim ID": submission.fineos_absence_id },
              },
              60000
            )
            .then(() => {
              cy.contains(submission.fineos_absence_id);
              // @todo removed for the time being waiting on the the long term solution.
              // cy.get(
              //   `a[href*="/employers/applications/status/?absence_id=${submission.fineos_absence_id}"]`
              // );
            });
        });
      });
    }
  );

  it(
    "Check the Claimant Portal for the legal notice (Appeal Acknowledgment).",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass([fineosSubmission, employerApproval]);
      portal.before();
      portal.loginClaimant();
      cy.unstash<Submission>("submission").then((submission) => {
        cy.task(
          "waitForClaimDocuments",
          {
            credentials: getClaimantCredentials(),
            application_id: submission.application_id,
            document_type: "Appeal Acknowledgment",
          },
          { timeout: 30000 }
        );
        portal.claimantGoToClaimStatus(submission.fineos_absence_id);
        cy.findByText("Appeal Acknowledgment (PDF)")
          .should("be.visible")
          .click({ force: true });
        // Hard-coded the `-AP-02` should make this more dynamic by stashing the Appeal subcase.
        // This can changed depending if its approved or denied claim.
        portal.downloadLegalNoticeSubcase(
          submission.fineos_absence_id,
          "-AP-02"
        );
      });
    }
  );
});
