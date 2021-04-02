import {
  beforePortal,
  beforeFineos,
  bailIfThisTestFails,
} from "../../../tests/common/before";
import { fineos, portal, email } from "../../../tests/common/actions";
import { getFineosBaseUrl, getLeaveAdminCredentials } from "../../../config";

describe("Employer Responses", () => {
  it("As an employer, I should recieve an email asking for my response to a claim and also fill out the ER form", () => {
    beforePortal();
    bailIfThisTestFails();

    cy.task("generateClaim", "BHAP1").then((claim) => {
      const { employer_fein } = claim.claim;
      if (!(typeof employer_fein === "string")) {
        throw new Error("No employer_fein property was added to this claim.");
      }
      cy.stash("claim", claim);
      cy.stash("timestamp_from", Date.now());
      const timestamp_from = Date.now();
      cy.task("submitClaimToAPI", claim).then((response) => {
        if (!response.fineos_absence_id) {
          throw new Error("Response does not have a fineos_absence_id");
        }
        // As an employer, I should receive a notification about my response being required
        cy.task<Email[]>(
          "getEmails",
          {
            address: "gqzap.notifications@inbox.testmail.app",
            subject: `Action required: Respond to ${claim.claim.first_name} ${claim.claim.last_name}'s paid leave application`,
            timestamp_from,
            debugInfo: { "Fineos Claim ID": response.fineos_absence_id },
          },
          { timeout: 180000 }
        ).then((emails) => {
          expect(emails.length).to.be.greaterThan(0);
          const email_match = emails.find((email) =>
            email.html.includes(response.fineos_absence_id as string)
          );
          if (!email_match) {
            throw new Error(
              `No emails quiered match the Finoes Absence ID:
                timestamp_from: ${timestamp_from} 
                fineos_absence_id: ${response.fineos_absence_id}`
            );
          }
          email.getNotificationData(email_match.html).then((data) => {
            expect(data.applicationId).to.equal(response.fineos_absence_id);
            expect(email_match.html).to.contain(
              `/employers/applications/new-application/?absence_id=${response.fineos_absence_id}`
            );
          });
        });

        // Access and fill out ER form
        cy.stash("fineos_absence_id", response.fineos_absence_id);
        cy.stash("applicationID", response.application_id);
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

  it(
    "In Fineos, I should see the employer's response recorded",
    { baseUrl: getFineosBaseUrl() },
    () => {
      beforeFineos();
      cy.unstash<string>("fineos_absence_id").then((claimNumber) => {
        cy.visit("/");
        fineos.visitClaim(claimNumber);
        fineos.assertClaimHasLeaveAdminResponse(true);
      });
    }
  );
});
