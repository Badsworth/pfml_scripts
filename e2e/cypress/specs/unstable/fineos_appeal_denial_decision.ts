import { portal, fineos, email, fineosPages } from "../../actions";
import { getFineosBaseUrl, getLeaveAdminCredentials } from "../../config";
import { assertValidClaim } from "../../../src/util/typeUtils";
import { Submission } from "../../../src/types";
describe("Create a new continuous leave, caring leave claim in FINEOS", () => {
  const fineosSubmission = it(
    "Should be able to create a claim",
    { baseUrl: getFineosBaseUrl() },
    () => {
      fineos.before();
      cy.visit("/");
      cy.task("generateClaim", "CDENY2").then((claim) => {
        cy.stash("claim", claim);
        assertValidClaim(claim.claim);
        fineosPages.ClaimantPage.visit(claim.claim.tax_identifier)
          .createNotification(claim.claim)
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
    }
  );

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

  it("CSR will deny claim", { baseUrl: getFineosBaseUrl() }, () => {
    cy.dependsOnPreviousPass([fineosSubmission, employerDenial]);
    fineos.before();
    cy.visit("/");
    cy.unstash<Submission>("submission").then(({ fineos_absence_id }) => {
      fineosPages.ClaimPage.visit(fineos_absence_id).deny(
        "Covered family relationship not established"
      );
    });
  });

  it(
    "CSR will process a decision change",
    { baseUrl: getFineosBaseUrl() },
    () => {
      cy.dependsOnPreviousPass([fineosSubmission, employerDenial]);
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
    "Check the Leave Admin email for the appeal notification.",
    { retries: 0 },
    () => {
      portal.before();
      cy.dependsOnPreviousPass([fineosSubmission, employerDenial]);
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
});
