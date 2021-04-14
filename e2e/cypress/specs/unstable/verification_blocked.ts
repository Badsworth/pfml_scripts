import * as portal from "../../tests/common/actions/portal";
import { beforePortal } from "../../tests/common/before";

describe("Leave Admin Self-Registration", () => {
  const register = it("Leave administrators should be able to self-register on the portal.", () => {
    beforePortal();
    cy.task("pickEmployer", { withholdings: [0, 0, 0, 0] }).then((employer) => {
      cy.task("generateCredentials").then((credentials) => {
        portal.registerAsLeaveAdmin(credentials, employer.fein);
        portal.login(credentials);
        portal.assertLoggedIn();
        cy.wait(1000);
        cy.get('button[type="submit"]').contains("Agree and continue").click();
        const withholding =
          employer.withholdings[employer.withholdings.length - 1];
        // portal.verifyLeaveAdmin(withholding);
      });
    });
  });
});
