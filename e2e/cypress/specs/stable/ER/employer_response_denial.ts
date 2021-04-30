import { fineos, portal, email } from "../../../actions";
import { getFineosBaseUrl, getLeaveAdminCredentials } from "../../../config";

describe("Employer Responses", () => {
  const submit = it("As an employer, I should recieve an email asking for my response to a claim and also fill out the ER form", () => {
    portal.before();

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
        email
          .getEmails(
            {
              address: "gqzap.notifications@inbox.testmail.app",
              subject: `Action required: Respond to ${claim.claim.first_name} ${claim.claim.last_name}'s paid leave application`,
              messageWildcard: response.fineos_absence_id,
              timestamp_from,
              debugInfo: { "Fineos Claim ID": response.fineos_absence_id },
            },
            180000
          )
          .then((emails) => {
            const data = email.getNotificationData(emails[0].html);
            expect(data.applicationId).to.equal(response.fineos_absence_id);
            expect(emails[0].html).to.contain(
              `/employers/applications/new-application/?absence_id=${response.fineos_absence_id}`
            );
          });

        // Access and fill out ER form
        cy.stash("fineos_absence_id", response.fineos_absence_id);
        cy.stash("applicationID", response.application_id);
        portal.login(getLeaveAdminCredentials(employer_fein));
        portal.respondToLeaveAdminRequest(
          response.fineos_absence_id,
          false,
          false,
          false
        );
      });
    });
  });

  it(
    "In Fineos, I should see the employer's response recorded",
    { baseUrl: getFineosBaseUrl() },
    () => {
      cy.dependsOnPreviousPass([submit]);
      fineos.before();
      cy.unstash<string>("fineos_absence_id").then((claimNumber) => {
        cy.visit("/");
        fineos.visitClaim(claimNumber);
        fineos.assertClaimStatus("Adjudication");
        fineos.assertClaimHasLeaveAdminResponse(false);
      });
    }
  );
});
