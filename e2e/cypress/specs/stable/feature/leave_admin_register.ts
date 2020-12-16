import * as portal from "../../../tests/common/actions/portal";
import { beforePortal } from "../../../tests/common/before";

describe("Leave Admin Self-Registration", () => {
  it("Leave administrators should be able to self-register on the portal.", () => {
    beforePortal();
    cy.task("generateCredentials", true).then((credentials) => {
      portal.registerAsLeaveAdmin(credentials);
      portal.login(credentials);
      portal.assertLoggedIn();
    });
  });
});
