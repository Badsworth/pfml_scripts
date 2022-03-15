import { portal, fineos, email, fineosPages } from "../../../actions";
import { getLeaveAdminCredentials } from "../../../config";
import { assertValidClaim } from "../../../../src/util/typeUtils";
import { Submission } from "../../../../src/types";
import { config } from "../../../actions/common";

describe("Create a new continuous leave, caring leave claim in FINEOS", () => {
  const fineosSubmission = it("Should be able to create a claim", () => {
    fineos.before();
    cy.task("generateClaim", "CDENY2").then((claim) => {
      cy.stash("claim", claim);
      assertValidClaim(claim.claim);
      fineosPages.ClaimantPage.visit(claim.claim.tax_identifier)
        .createNotification(
          claim.claim,
          claim.is_withholding_tax,
          config("HAS_APRIL_UPGRADE") === "true"
        )
        .then((fineos_absence_id) => {
          cy.log(fineos_absence_id);
          cy.stash("submission", {
            fineos_absence_id: fineos_absence_id,
            timestamp_from: Date.now(),
          });
          fineosPages.ClaimPage.visit(fineos_absence_id).adjudicate(
            (adjudication) => {
              adjudication.evidence((evidence) =>
                claim.documents.forEach(({ document_type }) =>
                  evidence.receive(document_type)
                )
              );
            }
          );
        });
    });
  });

  const employerDenial =
    it("Leave admin will submit ER denial for employee", () => {
      cy.dependsOnPreviousPass([fineosSubmission]);
      portal.before();
      cy.unstash<DehydratedClaim>("claim").then((claim) => {
        cy.unstash<Submission>("submission").then(({ fineos_absence_id }) => {
          assertValidClaim(claim.claim);
          portal.login(getLeaveAdminCredentials(claim.claim.employer_fein));
          portal.selectClaimFromEmployerDashboard(fineos_absence_id);
          portal.visitActionRequiredERFormPage(fineos_absence_id);
          portal.respondToLeaveAdminRequest(false, true, false, true);
        });
      });
    });

  it("CSR will deny claim", () => {
    cy.dependsOnPreviousPass([fineosSubmission, employerDenial]);
    fineos.before();
    cy.unstash<Submission>("submission").then(({ fineos_absence_id }) => {
      if (config("HAS_APRIL_UPGRADE") === "true") {
        fineosPages.ClaimPage.visit(fineos_absence_id).deny(
          "Covered family relationship not established",
          true,
          true
        );
      } else {
        fineosPages.ClaimPage.visit(fineos_absence_id).deny(
          "Covered family relationship not established",
          true,
          false
        );
      }
    });
  });

  const csrAppeal = it("CSR will process a decision change", () => {
    cy.dependsOnPreviousPass([fineosSubmission, employerDenial]);
    fineos.before();
    cy.unstash<DehydratedClaim>("claim").then((claim) => {
      cy.unstash<Submission>("submission").then(({ fineos_absence_id }) => {
        const claimPage = fineosPages.ClaimPage.visit(fineos_absence_id);
        claimPage.addAppeal(true);
        claimPage.addEmployer(<string>claim.claim.employer_fein);
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
    });
  });

  it(
    "Check the Leave Admin email for the appeal notification.",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass([fineosSubmission, employerDenial, csrAppeal]);
      portal.before();
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
              90000
            )
            .then(() => {
              cy.screenshot("denial-leave-admin-email");
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
    "Should generate a Appeal Acknowledgment that the Leave Admin can view",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass([fineosSubmission, employerDenial, csrAppeal]);
      portal.before();
      cy.unstash<Submission>("submission").then((submission) => {
        cy.unstash<string>("appeal_case_id").then((appeal_case_id) => {
          cy.unstash<DehydratedClaim>("claim").then((claim) => {
            if (!claim.claim.employer_fein) {
              throw new Error("Claim must include employer FEIN");
            }
            const employeeFullName = `${claim.claim.first_name} ${claim.claim.last_name}`;
            portal.loginLeaveAdmin(claim.claim.employer_fein);
            portal.selectClaimFromEmployerDashboard(
              submission.fineos_absence_id
            );
            portal.checkNoticeForLeaveAdmin(
              submission.fineos_absence_id,
              employeeFullName,
              "Appeal Acknowledgment (PDF)"
            );
            portal.downloadLegalNoticeSubcase(appeal_case_id);
          });
        });
      });
    }
  );
});
