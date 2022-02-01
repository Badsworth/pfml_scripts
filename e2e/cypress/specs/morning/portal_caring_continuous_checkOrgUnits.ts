import { fineos, fineosPages, portal } from "../../actions";
import { config } from "../../actions/common";
import { Submission } from "../../../src/types";
import { describeIf } from "../../util";

describeIf(
  config("HAS_ORGUNITS_SETUP") === "true",
  "Submit a claim through the Portal that has OrgUnits associated with the Employer",
  {},
  () => {
    it("As a claimant, I should be able to submit a claim application through the portal", () => {
      portal.before({
        claimantShowOrganizationUnits: true,
      });
      cy.task("generateClaim", {
        scenario: "ORGUNIT",
        employeePoolFileName: config("ORGUNIT_EMPLOYEES_FILE"),
      }).then((claim) => {
        cy.stash("claim", claim);
        const application: ApplicationRequestBody = claim.claim;
        const paymentPreference = claim.paymentPreference;
        portal.loginClaimant();
        portal.goToDashboardFromApplicationsPage();

        // Submit Claim
        portal.startClaim();
        portal.submitClaimPartOne(application, true);
        portal.waitForClaimSubmission().then((data) => {
          cy.stash("submission", {
            application_id: data.application_id,
            fineos_absence_id: data.fineos_absence_id,
            timestamp_from: Date.now(),
          });
        });
        portal.submitPartsTwoThreeNoLeaveCert(
          paymentPreference,
          claim.is_withholding_tax
        );
      });
    });

    it(
      "Check within FINEOS to see the same OrgUnit for the Employee",
      { retries: 0 },
      () => {
        cy.dependsOnPreviousPass();
        fineos.before();
        cy.unstash<DehydratedClaim>("claim").then((claim) => {
          cy.unstash<Submission>("submission").then(({ fineos_absence_id }) => {
            const department = claim.metadata?.orgunits as unknown as string;
            fineosPages.ClaimPage.visit(fineos_absence_id).adjudicate(
              (adjudication) => {
                adjudication.requestEmploymentInformation();
                cy.get('span[id$="_Organisation_Unit_Label"]').should(
                  (element) => {
                    expect(
                      element,
                      "Organization Unit should be the `${department}`"
                    ).to.have.text(`${department}`);
                  }
                );
              }
            );
          });
        });
      }
    );
  }
);
