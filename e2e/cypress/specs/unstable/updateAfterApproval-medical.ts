import { fineos, portal } from "../../actions";
import { getFineosBaseUrl } from "../../config";
import { Submission } from "../../../src/types";
import { extractLeavePeriod } from "../../../src/util/claims";

describe("Post-approval (notifications/notices)", { retries: 0 }, () => {
  after(() => {
    portal.deleteDownloadsFolder();
  });

  const credentials: Credentials = {
    username: Cypress.env("E2E_PORTAL_USERNAME"),
    password: Cypress.env("E2E_PORTAL_PASSWORD"),
  };

  it(
    "Create a financially eligible MEDICAL claim in which an employer will respond",
    { baseUrl: getFineosBaseUrl() },
    () => {
      fineos.before();
      cy.visit("/");
      // Submit a claim via the API, including Employer Response.
      cy.task("generateClaim", "MHAP1ER").then((claim) => {
        console.log(claim.claim);
        cy.stash("claim", claim.claim);
        cy.task("submitClaimToAPI", {
          ...claim,
          credentials,
        }).then((response) => {
          if (!response.fineos_absence_id) {
            throw new Error("Response contained no fineos_absence_id property");
          }
          const [, endDate] = extractLeavePeriod(claim.claim);
          cy.stash("submission", {
            application_id: response.application_id,
            fineos_absence_id: response.fineos_absence_id,
            timestamp_from: Date.now(),
          });
          fineos.claimAdjudicationFlow(
            response.fineos_absence_id,
            "Serious Health Condition - Employee",
            true
          );
          fineos.claimAddTimeAfterApproval(response.fineos_absence_id, endDate);
          fineos.claimExtensionAdjudicationFlow(response.fineos_absence_id);
        });
      });
    }
  );
  it("As an employer, I should receive a second notification about my response being required", () => {
    cy.unstash<Submission>("submission").then((submission) => {
      cy.unstash<ApplicationRequestBody>("claim").then((claim) => {
        // cy.wait(3000)
        cy.task<Email[]>(
          "getEmails",
          {
            address: "gqzap.notifications@inbox.testmail.app",
            subject: `Action required: Respond to ${claim.first_name} ${claim.last_name}'s paid leave application`,
            timestamp_from: submission.timestamp_from,
          },
          { timeout: 360000 }
        ).then((emails) => {
          expect(emails[0].html).to.contain(
            `/employers/applications/new-application/?absence_id=${submission.fineos_absence_id}`
          );
        });
      });
    });
  });
});
