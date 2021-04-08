import { beforePortal } from "../../tests/common/before";
import { portal, email } from "../../tests/common/actions";

describe("Employer Responses", () => {
  it("As an employer, I should receive an email asking for my response to a claim and also fill out the ER form", () => {
    cy.task("generateClaim", "BHAP1").then((claim) => {
      // Generate a claim and stash data about it
      const { employer_fein } = claim.claim;
      if (!(typeof employer_fein === "string")) {
        throw new Error("No employer_fein property was added to this claim.");
      }
      cy.stash("claim", claim);
      cy.stash("timestamp_from", Date.now());
      const timestamp_from = Date.now();

      beforePortal();

      // Create a new employee account
      cy.task("generateCredentials").then((credentials) => {
        portal.registerAsClaimant(credentials);
        portal.login(credentials);
        portal.assertLoggedIn();
        cy.get("[data-cy=consent-to-data-sharing-btn]").click();
        // TODO: Convert the employee account to an employer one
        // Click on Convert To Employer Banner link
        cy.get("[data-cy=convert-link]").click();
        cy.get("[data-cy=fein-input]").type(employer_fein);
        cy.get("[data-cy=fein-form]").submit();
        // TODO: Verify the employer account

        // Submit the generated claim to the API
        cy.task("submitClaimToAPI", claim).then((response) => {
          if (!response.fineos_absence_id) {
            throw new Error("Response does not have a fineos_absence_id");
          }
          // Get the email from the address of the account you just converted
          cy.task<Email[]>(
            "getEmails",
            {
              address: credentials.username,
              subject: `Action required: Respond to ${claim.claim.first_name} ${claim.claim.last_name}'s paid leave application`,
              messageWildcard: response.fineos_absence_id,
              timestamp_from,
              debugInfo: { "Fineos Claim ID": response.fineos_absence_id },
            },
            { timeout: 180000 }
          ).then((emails) => {
            const data = email.getNotificationData(emails[0].html);
            expect(data.applicationId).to.equal(response.fineos_absence_id);
            expect(emails[0].html).to.contain(
              `/employers/applications/new-application/?absence_id=${response.fineos_absence_id}`
            );
          });

          // Access and fill out ER form (already logged in as Employer)
          cy.stash("fineos_absence_id", response.fineos_absence_id);
          cy.stash("applicationID", response.application_id);
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
