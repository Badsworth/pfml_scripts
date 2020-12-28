import { fineos, portal, email } from "../../../tests/common/actions";
import { beforeFineos } from "../../../tests/common/before";
import { beforePortal } from "../../../tests/common/before";
import { getFineosBaseUrl, getLeaveAdminCredentials } from "../../../config";

describe("Approval (notificatins/notices)", () => {
  it("Create a financially eligible claim in which an employer will respond", () => {
    beforePortal();
    cy.visit("/");

    // Generate Creds for Registration/Login - submit claim via API
    cy.task("generateCredentials", false).then((credentials) => {
      cy.stash("credentials", credentials);
      cy.task("registerClaimant", credentials).then(() => {
        cy.task("generateClaim", {
          claimType: "BHAP1",
          employeeType: "financially eligible",
        }).then((claim: SimulationClaim) => {
          const { employer_fein } = claim.claim;
          cy.stash("employerFEIN", employer_fein);
          if (!(typeof employer_fein === "string")) {
            throw new Error(
              "No employer_fein property was added to this claim."
            );
          }
          cy.stash("claim", claim.claim);
          cy.stash("timestamp_from", Date.now());
          cy.task("submitClaimToAPI", {
            ...claim,
            credentials,
          } as SimulationClaim).then((response) => {
            console.log(response);
            cy.wrap(response.fineos_absence_id).as("fineos_absence_id");
            cy.stashLog("fineos_absence_id", response.fineos_absence_id);
            cy.stashLog("applicationId", response.application_id);

            // Complete Employer Response
            portal.login(getLeaveAdminCredentials(employer_fein));
            portal.respondToLeaveAdminRequest(
              response.fineos_absence_id,
              false,
              true,
              true
            );
          });
        });
      });
    });
  });

  // Check for ER and approval claim in Fineos
  it(
    "In Fineos, complete an Adjudication Approval",
    { baseUrl: getFineosBaseUrl() },
    () => {
      beforeFineos();
      cy.unstash<string>("fineos_absence_id").then((claimNumber) => {
        cy.visit("/");
        fineos.claimAdjudicationFlow(claimNumber, true);
      });
    }
  );

  // Check Legal Notice for both claimant/Leave-admin
  it("Checking Legal Notice for both claimant and Leave-Admin", () => {
    beforePortal();

    cy.unstash<Credentials>("credentials").then((credentials) => {
      portal.login(credentials);
      cy.unstash<string>("applicationId").then((applicationId) => {
        cy.log("Waiting for documents");
        cy.task(
          "waitForClaimDocuments",
          {
            credentials: credentials,
            applicationId: applicationId,
            document_type: "Approval Notice",
          },
          { timeout: 300000 }
        );
        cy.log("Finished waiting for documents");
      });
      cy.unstash<string>("fineos_absence_id").then((caseNumber) => {
        cy.visit("/applications");
        cy.contains("article", caseNumber).within(() => {
          cy.contains("a", "Approval notice").should("be.visible");
        });
        portal.logout();

        // Check Legal Notice for Leave-Admin
        cy.unstash<string>("employerFEIN").then((employer_fein) => {
          cy.unstash<ApplicationRequestBody>("claim").then((claim) => {
            const employeeFullName = `${claim.first_name} ${claim.last_name}`;
            portal.login(getLeaveAdminCredentials(employer_fein));
            portal.checkNoticeForLeaveAdmin(
              caseNumber,
              employeeFullName,
              "approval"
            );
          });
        });
      });
    });
  });

  // Check for email notification in regards to a claim approval
  it("Checking email notifications for both claimant and Leave-Admin", () => {
    cy.unstash<ApplicationRequestBody>("claim").then((claim) => {
      if (!claim.employer_fein || !claim.first_name || !claim.last_name) {
        throw new Error("This employer has no FEIN");
      }
      cy.unstash<string>("fineos_absence_id").then((caseNumber) => {
        cy.unstash<number>("timestamp_from").then((timestamp_from) => {
          const employeeFullName = `${claim.first_name} ${claim.last_name}`;
          const subjectEmployer = email.getNotificationSubject(
            employeeFullName,
            "approval (employer)",
            caseNumber
          );
          const subjectClaimant = email.getNotificationSubject(
            employeeFullName,
            "approval (claimant)",
            caseNumber
          );
          cy.log(subjectEmployer);
          cy.log(subjectClaimant);

          // Check email for Employer/Leave Admin
          cy.task<Email[]>(
            "getEmails",
            {
              address: "gqzap.notifications@inbox.testmail.app",
              subject: subjectEmployer,
              timestamp_from: timestamp_from,
            },
            { timeout: 180000 }
          ).then((emails) => {
            const emailContent = email.getNotificationData(emails[0].html);
            if (typeof claim.date_of_birth !== "string") {
              throw new Error("DOB must be a string");
            }
            const dob =
              claim.date_of_birth.replace(/-/g, "/").slice(5) + "/****";
            expect(emailContent.name).to.equal(employeeFullName);
            expect(emailContent.dob).to.equal(dob);
            expect(emailContent.applicationId).to.equal(caseNumber);
            expect(emails[0].html).to.contain(
              `/employers/applications/status/?absence_id=${caseNumber}`
            );
          });

          // Check email for Claimant/Employee
          cy.task<Email[]>(
            "getEmails",
            {
              address: "gqzap.notifications@inbox.testmail.app",
              subject: subjectClaimant,
              timestamp_from: timestamp_from,
            },
            { timeout: 180000 }
          ).then((emails) => {
            const emailContent = email.getNotificationData(emails[0].html);
            if (typeof claim.date_of_birth !== "string") {
              throw new Error("DOB must be a string");
            }
            expect(emailContent.applicationId).to.contain(caseNumber);
          });
        });
      });
    });
  });
});
