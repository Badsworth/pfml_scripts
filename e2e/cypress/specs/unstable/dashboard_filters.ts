import { portal } from "../../actions";
import { assertValidClaim } from "../../../src/util/typeUtils";
import {
  ReviewStatusOptions,
  ClaimantStatusFilters,
} from "../../actions/portal";

describe("Employer dashboard", () => {
  after(() => {
    portal.deleteDownloadsFolder();
  });
  const leave_status_filters: ClaimantStatusFilters[] = [
    "Denied",
    "Approved",
    "Cancelled",
    "Pending",
    "Withdrawn",
  ];
  const review_options: ReviewStatusOptions[] = [
    "Yes, review requested",
    "No, review not needed",
  ];

  const submit = it("Given a claim", () => {
    cy.task("generateClaim", "MED_INTER_INEL").then((claim) => {
      cy.stash("claim", claim.claim);
    });
  });

  it("LA should be able to view, filter, sort claims and search by name", () => {
    cy.dependsOnPreviousPass([submit]);
    portal.before();
    cy.unstash<ApplicationRequestBody>("claim").then((claim) => {
      assertValidClaim(claim);
      portal.loginLeaveAdmin(claim.employer_fein);
      portal.goToEmployerDashboard();
      cy.wait("@dashboardClaimQueries");
      review_options.forEach((review_option) => {
        portal.clickShowFilterButton();
        cy.findByLabelText(review_option).click({ force: true });
        portal.filterLADashboardBy(review_option, leave_status_filters);
      });
      portal.sortClaims("name_asc");
      portal.sortClaims("name_desc");
      portal.sortClaims("old");
      portal.sortClaims("new");
      // Test search by claim ID
      cy.get("table tbody")
        .should(($table) => {
          expect($table.children().length).to.be.gt(0);
        })
        .find('th[data-label="Employee (Application ID)"] .text-normal')
        .first()
        .then(($td) => {
          portal.searchClaims($td.text());
          portal.clearSearch();
        });
      // Test search by claimaint name
      cy.get("table tbody")
        .should(($table) => {
          expect($table.children().length).to.be.gt(0);
        })
        .find('th[data-label="Employee (Application ID)"] a')
        .then(($th) => {
          const names_element = $th.toArray();
          const names_only = names_element.map((el) => {
            const name = /^[^NTN]*/.exec(el.textContent as string);
            if (!name) throw new Error("Can't parse element text");
            return name[0];
          });
          const name_to_search = names_only.find((n) => n !== "--");
          if (!name_to_search) return; // No employee match will be found
          portal.searchClaims(name_to_search, false);
          portal.clearSearch();
        });
    });
  });
});
