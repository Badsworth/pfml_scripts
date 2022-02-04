import { portal } from "../../../actions";
import { config } from "../../../actions/common";
import { describeIf } from "../../../util";

describeIf(
  config("MFA_ENABLED") === "true",
  "Claimant Registration with MFA",
  {},
  () => {
    const register_mfa =
      it("As a newly registered user I should be prompted to enable MFA, then trigger MFA successfully", () => {
        portal.before();
        cy.task("generateCredentials").then((credentials) => {
          cy.stash("credentials", credentials);
          portal.registerAsClaimant(credentials);
          portal.loginClaimant(credentials);
          portal.assertLoggedIn();
          portal.consentDataSharing();
          portal.enableMFA();
          portal.completeFlowMFA("primary");
          portal.logout();
          portal.loginMFA(credentials, "primary");
        });
      });

    const update_mfa =
      it("As a user w/MFA enabled, I should be able to update my MFA phone number successfully", () => {
        cy.dependsOnPreviousPass([register_mfa]);
        portal.before();
        cy.unstash<Credentials>("credentials").then((credentials) => {
          portal.loginMFA(credentials, "primary");
          portal.updateNumberMFA();
          portal.logout();
          portal.loginMFA(credentials, "secondary");
        });
      });

    it("As a user w/MFA enabled, I should be able to successfuly disable my MFA phone number", () => {
      cy.dependsOnPreviousPass([register_mfa, update_mfa]);
      portal.before();
      cy.unstash<Credentials>("credentials").then((credentials) => {
        portal.loginMFA(credentials, "secondary");
        portal.disableMFA();
        portal.logout();
        portal.loginClaimant(credentials);
        portal.assertLoggedIn();
      });
    });
  }
);
