import * as portal from "../../tests/common/actions/portal";
import { beforePortal } from "../../tests/common/before";

describe("Leave Admin Self-Registration", () => {
  it("Leave administrators should be able to self-register on the portal.", () => {
    beforePortal();
    cy.task("generateLeaveAdminCredentials").then((credentials) => {
      portal.registerAsLeaveAdmin(credentials);
      portal.login(credentials);
      portal.assertLoggedIn();
      cy.wait(1000);
      cy.get('button[type="submit"]').contains("Agree and continue").click();
      portal.verifyLeaveAdmin("60000");
    });
  });
});
