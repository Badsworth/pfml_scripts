import { portal } from "../../actions";
// import { beforePortal } from "../../tests/common/before";

describe("Leave Admin Self-Registration", () => {
  it("Leave administrators should be able to self-register on the portal.", () => {
    portal.before();
    cy.task("pickEmployer", {
      withholdings: [0, 0, 0, 0],
      metadata: { register_leave_admins: true },
    }).then((employer) => {
      cy.task("generateCredentials").then((credentials) => {
        portal.registerAsLeaveAdmin(credentials, employer.fein);
        portal.login(credentials);
        portal.assertLoggedIn();
        cy.wait(1000);
        cy.get('button[type="submit"]').contains("Agree and continue").click();
        const withholding =
          employer.withholdings[employer.withholdings.length - 1];
        if (typeof withholding !== "number")
          throw new Error("This employer has no withholdings reported");
        portal.verifyLeaveAdmin(withholding);
      });
    });
  });
});
