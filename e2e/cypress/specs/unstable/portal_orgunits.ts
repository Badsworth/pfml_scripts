import { fineos, fineosPages, portal } from "../../actions";
import { config } from "../../actions/common"
import {Submission} from "../../../src/types";
import EmployeePool from "../../../src/generation/Employee";
import {getDocumentReviewTaskName} from "../../../src/util/documents";
import {onTab} from "../../actions/fineos";
import {getEmployeePool} from "../../../src/util/common";

Cypress.env({
  "ORGUNIT_EMPLOYEES_FILE": "./employees/e2e-2021-12-20-orgunits.employees.json",
  "ORGUNIT_EMPLOYERS_FILE": "./employers/e2e-2021-12-20-orgunits.json",
});

describe("Submit a claim through the Portal that has OrgUnits associated with the Employer", () => {
  // before(async () => employeePool = await EmployeePool.load(config("ORGUNIT_EMPLOYEES_FILE")))
  it("As a claimant, I should be able to submit a claim application through the portal", () => {
    portal.before({
        claimantShowOrganizationUnits:
          config("ORGUNITS_SETUP") === "true",
      });
    cy.task("generateClaim", "ORGUNIT").then((claim) => {
      cy.stash("claim", claim);
      const application: ApplicationRequestBody = claim.claim;
      const paymentPreference = claim.paymentPreference;
      portal.loginClaimant();
      portal.goToDashboardFromApplicationsPage();

      // Submit Claim
      portal.startClaim();
      portal.submitClaimPartOne(application);
      portal.waitForClaimSubmission().then((data) => {
        cy.stash("submission", {
          application_id: data.application_id,
          fineos_absence_id: data.fineos_absence_id,
          timestamp_from: Date.now(),
        });
      });
      // portal.submitClaimPartsTwoThree(application, paymentPreference);
    });
  });

  it(
    "Check in FINEOS to see the same OrgUnit for the Employee",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass();
      fineos.before();
      cy.unstash<Submission>("submission").then(({ fineos_absence_id }) => {
        cy.unstash<DehydratedClaim>("claim").then((claim) => {
          fineosPages.ClaimPage.visit(fineos_absence_id)
            .adjudicate((adjudication) => {
              adjudication.requestEmploymentInformation()
              cy.findByLabelText("Organization Unit").should((input) => {
                expect(
                  input,
                  `Organization Unit should be the Division of Administrative Law Appeals`
                )
                  .attr("value")
                  .equal(String("Division of Administrative Law Appeals"));
              });
            })
          })

      });
    }
  );
})
