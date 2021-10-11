import { portal } from "../../../actions";
import { assertValidClaim } from "../../../../src/util/typeUtils";
import {
  DashboardClaimStatus,
  FilterOptionsFlags,
} from "../../../actions/portal";

describe("Employer dashboard", () => {
  after(() => {
    portal.deleteDownloadsFolder();
  });
  const submit = it("Given a claim", () => {
    cy.task("generateClaim", "MED_INTER_INEL").then((claim) => {
      cy.stash("claim", claim.claim);
    });
  });
  it("LA should be able to view, filter, sort claims and search by name", () => {
    cy.dependsOnPreviousPass([submit]);
    portal.before();
    cy.visit("/");
    cy.unstash<ApplicationRequestBody>("claim").then((claim) => {
      assertValidClaim(claim);
      portal.loginLeaveAdmin(claim.employer_fein);
      portal.goToEmployerDashboard();
      const filter_checks: FilterOptionsFlags = {
        "Review by": true,
        "No action required": true,
        Closed: true,
        Denied: true,
        Approved: true,
      };
      cy.wait("@dashboardClaimQueries");
      Object.entries(filter_checks).forEach(([key, value]) => {
        portal.filterLADashboardBy({
          status: {
            [key]: value,
          },
        });
        if (value) {
          portal.assertClaimsHaveStatus(key as DashboardClaimStatus);
          portal.clearFilters();
        }
      });
      portal.sortClaims("name_asc");
      portal.sortClaims("name_desc");
      portal.sortClaims("old");
      portal.sortClaims("new");
      portal.sortClaims("status");
      cy.get("table tbody")
        .should(($table) => {
          expect($table.children().length).to.be.gt(0);
        })
        .find('td[data-label="Application ID"]')
        .first()
        .then(($td) => {
          portal.searchClaims($td.text());
        });
    });
  });
});
