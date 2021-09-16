import { portal } from "../../../actions";
import { assertValidClaim } from "../../../../src/util/typeUtils";
import { DashboardClaimStatus } from "../../../actions/portal";

describe("Employer dashboard", () => {
  after(() => {
    portal.deleteDownloadsFolder();
  });
  const submit = it("Given a claim", () => {
    cy.task("generateClaim", "MED_INTER_INEL").then((claim) => {
      cy.stash("claim", claim.claim);
    });
  });
  it("LA should be able to view, filter, and sort claims", () => {
    cy.dependsOnPreviousPass([submit]);
    portal.before();
    cy.visit("/");
    cy.unstash<ApplicationRequestBody>("claim").then((claim) => {
      assertValidClaim(claim);
      portal.loginLeaveAdmin(claim.employer_fein);
      portal.goToEmployerDashboard();
      const statuses: DashboardClaimStatus[] = [
        "Review by",
        "No action required",
        "Closed",
        "Denied",
        // Leaving this out, as currently Leave Admins are not able to respond to subsequent leave requests, which causes some "Approved" claims to show up as "Review by"
        // @see PFMLPB-1558
        // "Approved"
      ];
      cy.wait("@dashboardClaimQueries");
      statuses.forEach((status) => {
        portal.filterLADashboardBy({
          status: {
            [status]: true,
          },
        });
        portal.assertClaimsHaveStatus(status);
        portal.clearFilters();
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
