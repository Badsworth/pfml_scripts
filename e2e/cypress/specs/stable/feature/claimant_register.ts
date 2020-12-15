import * as portal from "../../../tests/common/actions/portal";
import { beforePortal } from "../../../tests/common/before";

describe("Claimant Registration", () => {
  beforeEach(beforePortal);

  it("Should allow a new claimant to register", () => {
    cy.task("generateCredentials", false).then((credentials) => {
      portal.registerAsClaimant(credentials);
      portal.login(credentials);
      portal.assertLoggedIn();
    });
  });
});
