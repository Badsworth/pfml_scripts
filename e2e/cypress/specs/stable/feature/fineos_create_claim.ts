import { fineos } from "../../../tests/common/actions";
import { beforeFineos } from "../../../tests/common/before";
import { extractLeavePeriod } from "../../../../src/utils";
import { getFineosBaseUrl } from "../../../config";

describe("Create a new continuous leave, bonding claim in FINEOS", () => {
  before(beforeFineos);
  it(
    "Should be able to create a claim",
    { baseUrl: getFineosBaseUrl() },
    () => {
      cy.task("generateClaim", {
        claimType: "BHAP1",
        employeeType: "financially eligible",
      }).then((claim: SimulationClaim) => {
        cy.log("generated claim", claim.claim);
        if (!claim.claim.first_name || !claim.claim.last_name) {
          throw new Error("Claim does not have a first or last name.");
        }

        cy.visit("/");
        fineos.searchClaimant(claim.claim.first_name, claim.claim.last_name);
        fineos.clickBottomWidgetButton("OK");
        fineos.assertOnClaimantPage(
          claim.claim.first_name,
          claim.claim.last_name
        );
        const [startDate, endDate] = extractLeavePeriod(claim.claim);
        fineos.createNotification(startDate, endDate);
      });
    }
  );
});
