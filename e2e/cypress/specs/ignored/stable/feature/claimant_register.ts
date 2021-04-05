import * as portal from "../../../../tests/common/actions/portal";
import { beforePortal } from "../../../../tests/common/before";

describe("Claimant Registration", () => {
  it("Should allow a new claimant to register", () => {
    beforePortal();
    cy.task("generateCredentials").then((credentials) => {
      portal.registerAsClaimant(credentials);
      portal.login(credentials);
      portal.assertLoggedIn();
    });
  });
});
