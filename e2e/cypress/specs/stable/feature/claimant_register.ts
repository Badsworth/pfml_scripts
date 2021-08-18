import { portal, fineos, fineosPages } from "../../../actions";

describe("Claimant Registration", () => {
  it("Should allow a new claimant to register", () => {
    portal.before();
    cy.task("generateCredentials").then((credentials) => {
      portal.registerAsClaimant(credentials);
      portal.login(credentials);
      portal.assertLoggedIn();
    });
  });
});
