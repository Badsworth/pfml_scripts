import { portal } from "../../../actions";
import { assertValidClaim } from "../../../../src/util/typeUtils";
import {
  DashboardClaimStatus,
  FilterOptionsFlags,
} from "../../../actions/portal";
import { config } from "../../../actions/common";

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
    const checkStatus = config("HAS_CLAIMANT_STATUS_PAGE") === "true";
    const isStage = config("ENVIRONMENT") === "stage";
    portal.before({ employerShowReviewByStatus: checkStatus });
    cy.visit("/");
    cy.unstash<ApplicationRequestBody>("claim").then((claim) => {
      assertValidClaim(claim);
      portal.loginLeaveAdmin(claim.employer_fein);
      portal.goToEmployerDashboard();
      const filter_checks: FilterOptionsFlags = {
        "Review by": checkStatus,
        "No action required": checkStatus,
        // These flags are present because the below filters will fail when
        // ff: employerShowReviewByStatus is enabled.  @see https://lwd.atlassian.net/browse/EDM-283
        // Once EDM is resolved we can "turn on" the below filters.
        Closed: isStage,
        Denied: isStage,
        // Leaving this out, as currently Leave Admins are not able to respond to subsequent leave requests, which causes some "Approved" claims to show up as "Review by"
        // @see PFMLPB-1558
        // Approved: true
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
      checkStatus && portal.sortClaims("status");
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
