import { portal, fineos, email, fineosPages } from "../../actions";
import { getClaimantCredentials, getFineosBaseUrl, getLeaveAdminCredentials } from "../../config";
import { assertValidClaim } from "../../../src/util/typeUtils";
import { Submission } from "../../../src/types";
import { config } from "../../actions/common";

describe("Submit a claim through Portal: Verify it creates an absence case in Fineos", () => {
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
    it("Leave admin will submit ER denial for employee", () => {
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

  it("CSR will deny claim", { baseUrl: getFineosBaseUrl() }, () => {
    cy.dependsOnPreviousPass([fineosSubmission]);
    fineos.before();
    cy.visit("/");
    cy.unstash<Submission>("submission").then(({ fineos_absence_id }) => {
      fineosPages.ClaimPage.visit(fineos_absence_id)
        .deny("Covered family relationship not established")
        .triggerNotice("Leave Request Declined")
    });
    cy.screenshot("Fineos Absence Case");
  });

  it(
    "CSR will process the appeal for schedule hearing",
    { baseUrl: getFineosBaseUrl() },
    () => {
      cy.dependsOnPreviousPass([fineosSubmission]);
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
      cy.dependsOnPreviousPass([fineosSubmission]);
      cy.unstash<Submission>("submission").then((submission) => {
        cy.unstash<ApplicationRequestBody>("claim").then((claim) => {
          const subjectClaimant = email.getNotificationSubject(
            `${claim.first_name} ${claim.last_name}`,
            "appeal (claimant)",
            submission.fineos_absence_id
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
          cy.get(`a[href*="${config("PORTAL_BASEURL")}/applications"]`);
          cy.screenshot("Claimant Email");
        });
      });
    }
    });

  it("Check the Leave Admin email for the appeal notification.",
    { retries: 0 },
    () => {
      portal.before();
      cy.dependsOnPreviousPass([fineosSubmission]);
      cy.unstash<DehydratedClaim>("claim").then((claim) => {
        cy.unstash<Submission>("submission").then((submission) => {
          assertValidClaim(claim.claim);
          portal.loginLeaveAdmin(claim.claim.employer_fein);
          portal.selectClaimFromEmployerDashboard(submission.fineos_absence_id);
          const subjectEmployer = email.getNotificationSubject(
            `${claim.claim.first_name} ${claim.claim.last_name}`,
            "appeal (employer)",
            submission.fineos_absence_id
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
              cy.get(
                `a[href*="/employers/applications/status/?absence_id=${submission.fineos_absence_id}"]`
              );
              cy.screenshot("Leave Admin Email");
            });
        });
      });
    }
  );

  // it("Check the Claimant Portal for the legal notice (Appeal Acknowledgment).",
  //   { retries: 0 },
  //   () => {
  //   cy.dependsOnPreviousPass([fineosSubmission]);
  //   portal.before({
  //     claimantShowStatusPage: config("HAS_CLAIMANT_STATUS_PAGE") === "true",
  //   });
  //   portal.loginClaimant();
  //   cy.unstash<Submission>("submission").then((submission) => {
  //     if (config("HAS_CLAIMANT_STATUS_PAGE") === "true") {
  //       portal.claimantGoToClaimStatus(submission.fineos_absence_id);
  //       portal.claimantAssertClaimStatus([
  //         {leave: "Care for a Family Member", status: "Denied"},
  //       ]);
  //       cy.screenshot("Claimant Portal Claim Status");
  //     } else {
  //       cy.task("waitForClaimDocuments",
  //         {
  //           credentials: getClaimantCredentials(),
  //           application_id: submission.application_id,
  //           document_type: "Appeal Acknowledgment",
  //         },
  //         { timeout: 30000 }
  //       );
  //       cy.contains("article", submission.fineos_absence_id).within(() => {
  //         cy.findByText("Appeal Acknowledgment (PDF)").should("be.visible").click();
  //       });
  //       portal.downloadLegalNotice(submission.fineos_absence_id);
  //     }
  //   });
  // });
});
