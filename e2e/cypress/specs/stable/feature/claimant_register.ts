import { beforePortal } from "../../../tests/common/before";

describe("Claimant Registration", () => {
  it("Should allow a new claimant to register", () => {
    beforePortal();
    cy.task("generateCredentials", false).then((credentials) => {
      cy.task("registerClaimant", credentials).then(() => {
        cy.task("generateClaim", {
          claimType: "BHAP1",
          employeeType: "financially eligible",
        }).then((claim: SimulationClaim) => {
          cy.task("submitClaimToAPI", { ...claim, credentials }).then(
            (response) => {
              console.log(response);
            }
          );
        });
      });
    });
  });
});
