import { Submission } from "../../../../src/types";
import { email, fineos, fineosPages, portal } from "../../../actions";
import { config } from "../../../actions/common";
import { getClaimantCredentials } from "../../../config";

describe("Create a Max Weekly Benefit Change Notice in FINEOS and check delivery to the LA/Claimant portal", () => {
  after(() => {
    portal.deleteDownloadsFolder();
  });

  it("Submits a claim via the API", () => {
    cy.task("generateClaim", "CCAP90ER").then((claim) => {
      cy.stash("claim", claim);
      cy.task("submitClaimToAPI", claim).then((res) => {
        cy.stash("submission", {
          application_id: res.application_id,
          fineos_absence_id: res.fineos_absence_id,
          timestamp_from: Date.now(),
        });
      });
    });
  });

  const approval = it("Submits a familial caring claim via the API", () => {
    fineos.before();
    cy.unstash<DehydratedClaim>("claim").then((claim) => {
      cy.unstash<Submission>("submission").then((response) => {
        cy.tryCount().then((tryCount) => {
          if (!response.fineos_absence_id) {
            throw new Error("Response contained no fineos_absence_id property");
          }
          const claimPage = fineosPages.ClaimPage.visit(
            response.fineos_absence_id
          );
          if (tryCount > 0) {
            fineos.assertClaimStatus("Approved");
            claimPage.triggerNotice("Designation Notice");
            return;
          }
          claimPage.adjudicate((adjudication) => {
            adjudication
              .evidence((evidence) => {
                for (const document of claim.documents) {
                  evidence.receive(document.document_type);
                }
              })
              .certificationPeriods((certificationPeriods) =>
                certificationPeriods.prefill()
              )
              .acceptLeavePlan();
          });
          claimPage.approve("Approved", config("HAS_APRIL_UPGRADE") === "true");
          claimPage.triggerNotice("Designation Notice");
        });
      });
    });
  });

  const notification =
    it("CSR will generate a maximum weekly benefit amount notice", () => {
      cy.dependsOnPreviousPass([approval]);
      fineos.before();
      cy.unstash<Submission>("submission").then(({ fineos_absence_id }) => {
        fineosPages.ClaimPage.visit(fineos_absence_id).paidLeave(
          (paidLeavePage) =>
            paidLeavePage
              .createCorrespondenceDocument(
                "Maximum Weekly Benefit Change Notice"
              )
              .documents((documentsPage) =>
                documentsPage
                  .assertDocumentExists("Maximum Weekly Benefit Change Notice")
                  .properties(
                    "Maximum Weekly Benefit Change Notice",
                    (propertiesPage) => propertiesPage.setStatus("Completed")
                  )
                  .properties(
                    "Maximum Weekly Benefit Change Notice",
                    (propertiesPage) =>
                      propertiesPage.fileNameShouldMatch(/.pdf$/)
                  )
              )
              .triggerPaidLeaveNotice("Maximum Weekly Benefit Change Notice")
        );
      });
    });

  it("Check the leave admin portal for the max weekly benefit change notice and download it", () => {
    cy.dependsOnPreviousPass([approval, notification]);
    portal.before();
    cy.unstash<Submission>("submission").then((submission) => {
      cy.unstash<DehydratedClaim>("claim").then(({ claim }) => {
        if (!claim.employer_fein) {
          throw new Error("Claim must include employer FEIN");
        }
        const employeeFullName = `${claim.first_name} ${claim.last_name}`;
        portal.loginLeaveAdmin(claim.employer_fein);
        portal.selectClaimFromEmployerDashboard(submission.fineos_absence_id);
        portal.checkNoticeForLeaveAdmin(
          submission.fineos_absence_id,
          employeeFullName,
          "Maximum Weekly Benefit Change Notice (PDF)"
        );
        portal.downloadLegalNotice(submission.fineos_absence_id);
      });
    });
  });

  it("Check the claimant portal for the max weekly benefit change notice and download it", () => {
    cy.dependsOnPreviousPass([approval, notification]);
    portal.before();
    cy.unstash<Submission>("submission").then((submission) => {
      portal.loginClaimant();
      cy.log("Waiting for documents");
      cy.task(
        "waitForClaimDocuments",
        {
          credentials: getClaimantCredentials(),
          application_id: submission.application_id,
          document_type: "Maximum Weekly Benefit Change Notice",
        },
        { timeout: 45000 }
      );
      cy.log("Finished waiting for documents");

      portal.claimantGoToClaimStatus(submission.fineos_absence_id);
      portal.claimantAssertClaimStatus([
        {
          leave: "Care for a Family Member",
          status: "Approved",
        },
      ]);
      cy.findByText("Maximum Weekly Benefit Change Notice (PDF)")
        .should("be.visible")
        .click({ force: true });
      portal.downloadLegalNotice(submission.fineos_absence_id);
    });
  });

  it("Claimant receives max weekly benefit change notification", () => {
    cy.dependsOnPreviousPass([approval, notification]);
    cy.unstash<Submission>("submission").then((submission) => {
      const portalPath = `/applications/status/?absence_case_id=${submission.fineos_absence_id}#view-notices`;
      email
        .getEmails({
          address: "gqzap.notifications@inbox.testmail.app",
          subject: email.getNotificationSubject("appeal (claimant)"),
          messageWildcard: portalPath,
          timestamp_from: submission.timestamp_from,
          debugInfo: { "Fineos Claim ID": submission.fineos_absence_id },
        })
        .then(() => {
          cy.contains("Your maximum weekly benefit has changed");
          cy.get(`a[href$='${portalPath}']`);
        });
    });
  });

  it("Leave admin receives max weekly benefit change notification", () => {
    cy.dependsOnPreviousPass([approval, notification]);
    cy.unstash<Submission>("submission").then((submission) => {
      const portalPath = `/employers/applications/status/?absence_id=${submission.fineos_absence_id}`;
      email
        .getEmails(
          {
            address: "gqzap.notifications@inbox.testmail.app",
            subject: email.getNotificationSubject("appeal (claimant)"),
            messageWildcard: portalPath,
            timestamp_from: submission.timestamp_from,
            debugInfo: { "Fineos Claim ID": submission.fineos_absence_id },
          },
          90000
        )
        .then(() => {
          cy.contains("The applicant’s maximum weekly benefit was changed.");
          cy.get(`a[href*='${portalPath}']`);
        });
    });
  });
});
