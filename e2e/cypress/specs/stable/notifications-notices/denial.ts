import { fineos, portal, email } from "../../../tests/common/actions";
import { beforeFineos, beforePortal } from "../../../tests/common/before";
import { getFineosBaseUrl, getLeaveAdminCredentials } from "../../../config";
import { ApplicationResponse } from "../../../../src/api";
import { Submission } from "../../../../src/types";

describe("Denial Notification and Notice", () => {
  const submit = it("Submit a financially ineligible claim to API", () => {
    beforePortal();

    cy.visit("/");
    cy.task("generateCredentials").then((credentials) => {
      cy.task("registerClaimant", credentials).then(() => {
        cy.task("generateClaim", "BHAP1INEL").then((claim) => {
          cy.task("submitClaimToAPI", {
            ...claim,
            credentials,
          }).then((responseData: ApplicationResponse) => {
            if (!responseData.fineos_absence_id) {
              throw new Error("FINEOS ID must be specified");
            }
            cy.stash("claim", claim.claim);
            cy.stash("submission", {
              application_id: responseData.application_id,
              fineos_absence_id: responseData.fineos_absence_id,
              timestamp_from: Date.now(),
            });
            cy.stash("credentials", credentials);
          });
        });
      });
    });
  });

  const adjudicate = it(
    "Deny a claim",
    { baseUrl: getFineosBaseUrl(), retries: 0 },
    () => {
      cy.dependsOnPreviousPass([submit]);
      beforeFineos();
      cy.visit("/");
      cy.unstash<Submission>("submission").then((submission) => {
        fineos.visitClaim(submission.fineos_absence_id);
        fineos.assertClaimFinancialEligibility(false);
      });
      fineos.denyClaim("Claimant wages failed 30x rule");
      cy.wait(200);
      fineos.triggerNoticeRelease("Denial Notice");
    }
  );

  // Check Legal Notice for both claimant/Leave-admin
  it(
    "Checking Legal Notice for both claimant and Leave-Admin",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass([submit, adjudicate]);
      beforePortal();
      cy.unstash<Credentials>("credentials").then((credentials) => {
        cy.unstash<Submission>("submission").then((submission) => {
          portal.login(credentials);
          cy.log("Waiting for documents");
          cy.task(
            "waitForClaimDocuments",
            {
              credentials: credentials,
              application_id: submission.application_id,
              document_type: "Denial Notice",
            },
            { timeout: 300000 }
          );
          cy.log("Finished waiting for documents");
          cy.visit("/applications");
          cy.contains("article", submission.fineos_absence_id).within(() => {
            cy.contains("a", "Denial notice").should("be.visible");
          });
          portal.logout();

          // Check Legal Notice for Leave-Admin
          cy.unstash<ApplicationRequestBody>("claim").then((claim) => {
            const employeeFullName = `${claim.first_name} ${claim.last_name}`;
            if (typeof claim.employer_fein !== "string") {
              throw new Error("Claim must include employer FEIN");
            }
            portal.login(getLeaveAdminCredentials(claim.employer_fein));
            portal.checkNoticeForLeaveAdmin(
              submission.fineos_absence_id,
              employeeFullName,
              "denial"
            );
          });
        });
      });
    }
  );

  it(
    "I should receive an 'denial (employer)' and 'denial (claimant)' notification",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass([submit, adjudicate]);
      cy.unstash<ApplicationRequestBody>("claim").then((claim) => {
        cy.unstash<Submission>("submission").then((submission) => {
          const employeeFullName = `${claim.first_name} ${claim.last_name}`;
          const subjectEmployer = email.getNotificationSubject(
            employeeFullName,
            "denial (employer)",
            submission.application_id
          );

          const subjectClaimant = email.getNotificationSubject(
            employeeFullName,
            "denial (claimant)",
            submission.application_id
          );

          cy.log(subjectEmployer);
          cy.log(subjectClaimant);

          cy.task<Email[]>(
            "getEmails",
            {
              address: "gqzap.notifications@inbox.testmail.app",
              subject: subjectEmployer,
              timestamp_from: submission.timestamp_from,
              messageWildcard: submission.fineos_absence_id,
              debugInfo: { "Fineos Claim ID": submission.fineos_absence_id },
            },
            { timeout: 180000 }
          ).then(async (emails) => {
            const data = email.getNotificationData(emails[0].html);
            const dob =
              claim.date_of_birth?.replace(/-/g, "/").slice(5) + "/****";
            expect(data.name).to.equal(employeeFullName);
            expect(data.dob).to.equal(dob);
            expect(data.applicationId).to.equal(submission.fineos_absence_id);
            expect(emails[0].html).to.contain(
              `/employers/applications/status/?absence_id=${submission.fineos_absence_id}`
            );
          });

          // Check email for Claimant
          cy.task<Email[]>("getEmails", {
            address: "gqzap.notifications@inbox.testmail.app",
            subject: subjectClaimant,
            timestamp_from: submission.timestamp_from,
            debugInfo: { "Fineos Claim ID": submission.fineos_absence_id },
          }).should("not.be.empty");
        });
      });
    }
  );
});
