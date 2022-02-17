import { portal } from "../../../actions";
import { config } from "../../../actions/common";
import { describeIf } from "../../../util";

const twilioNumber = (index: number): string => {
  const numbers = config("TWILIO_NUMBERS").split(",");
  if (typeof numbers[index] !== "string" || numbers[index].length < 1) {
    throw new Error(
      `TWILIO_NUMBERS does not include an element for index ${index}.`
    );
  }
  return numbers[index];
};

describeIf(
  config("MFA_ENABLED") === "true",
  "Claimant Registration with MFA",
  {},
  () => {
    const primary = twilioNumber(0);
    const secondary = twilioNumber(1);

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
          portal.completeFlowMFA(primary);
          portal.logout();
          portal.loginMFA(credentials, primary);
        });
      });

    const update_mfa =
      it("As a user w/MFA enabled, I should be able to update my MFA phone number successfully", () => {
        cy.dependsOnPreviousPass([register_mfa]);
        portal.before();
        cy.unstash<Credentials>("credentials").then((credentials) => {
          portal.loginMFA(credentials, primary);
          portal.updateNumberMFA(secondary);
          portal.logout();
          portal.loginMFA(credentials, secondary);
        });
      });

    it("As a user w/MFA enabled, I should be able to successfuly disable my MFA phone number", () => {
      cy.dependsOnPreviousPass([register_mfa, update_mfa]);
      portal.before();
      cy.unstash<Credentials>("credentials").then((credentials) => {
        portal.loginMFA(credentials, secondary);
        portal.disableMFA();
        portal.logout();
        portal.loginClaimant(credentials);
        portal.assertLoggedIn();
      });
    });
  }
);
