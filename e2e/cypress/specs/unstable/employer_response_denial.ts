import { beforePortal, beforeFineos } from "../../tests/common/before";
import { fineos, portal } from "../../tests/common/actions";
import { getFineosBaseUrl, getLeaveAdminCredentials } from "../../config";

describe("Employer Responses", () => {
  it("As an employer, I should be able to submit a response for a claim immediately after submission", () => {
    beforePortal();
    cy.task("generateClaim", {
      claimType: "BHAP1",
      employeeType: "financially eligible",
    }).then((claim) => {
      const { employer_fein } = claim.claim;
      if (!(typeof employer_fein === "string")) {
        throw new Error("No employer_fein property was added to this claim.");
      }
      cy.stash("claim", claim);
      cy.stash("timestamp_from", Date.now());
      cy.task("submitClaimToAPI", claim).then((response) => {
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
      beforeFineos();
      cy.unstash<string>("fineos_absence_id").then((claimNumber) => {
        cy.visit("/");
        fineos.visitClaim(claimNumber);
        fineos.assertClaimHasLeaveAdminResponse(false);
      });
    }
  );

  it("As an employer, I should receive a notification about my response being required", () => {
    cy.unstash<SimulationClaim>("claim").then((claim) => {
      if (
        !claim.claim.employer_fein ||
        !claim.claim.first_name ||
        !claim.claim.last_name
      ) {
        throw new Error("This employer has no FEIN");
      }
      cy.unstash<string>("fineos_absence_id").then((caseNumber) => {
        cy.unstash<number>("timestamp_from").then((timestamp_from) => {
          cy.task("getEmails", {
            address: "gqzap.notifications@inbox.testmail.app",
            subject: `Action required: Respond to ${claim.claim.first_name} ${claim.claim.last_name}'s paid leave application`,
            timestamp_from,
          }).then((emails) => {
            expect(emails.length).to.be.greaterThan(0);
            expect(emails[0].html).to.contain(
              `/employers/applications/new-application/?absence_id=${caseNumber}`
            );
          });
        });
      });
    });
  });
});
