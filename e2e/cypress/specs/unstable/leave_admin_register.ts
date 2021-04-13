import * as portal from "../../tests/common/actions/portal";
import { beforePortal } from "../../tests/common/before";

describe("Leave Admin Self-Registration", () => {
  const register = it("Leave administrators should be able to self-register on the portal.", () => {
    beforePortal();
    cy.task("pickEmployer", { withholdings: "non-exempt" }).then((employer) => {
      cy.task("generateCredentials").then((credentials) => {
        portal.registerAsLeaveAdmin(credentials, employer.fein);
        portal.login(credentials);
        portal.assertLoggedIn();
        cy.wait(1000);
        cy.get('button[type="submit"]').contains("Agree and continue").click();
        const withholding =
          employer.withholdings[employer.withholdings.length - 1];
        if (!withholding)
          throw new Error("This employer has no withholdings reported");
        portal.verifyLeaveAdmin(withholding);

        cy.stash("employer", employer.fein);
        cy.stash("credentials", credentials);
      });
    });
  });

  it("Leave administrators should be able to register for a second organization", () => {
    cy.dependsOnPreviousPass([register]);
    beforePortal();
    cy.unstash<Credentials>("credentials").then((credentials) => {
      cy.unstash<string>("employer").then((fein) => {
        portal.login(credentials);
        cy.contains("Your organizations").click();
        // Pick a second employer from the dataset to register as an additional organization.
        cy.task("pickEmployer", {
          withholdings: "non-exempt",
          notFEIN: fein,
        }).then((secondary) => {
          const secondaryWithholding =
            secondary.withholdings[secondary.withholdings.length - 1];
          portal.addOrganization(secondary.fein, secondaryWithholding);
        });
      });
    });
  });
});
