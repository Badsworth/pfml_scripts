import { Submission } from "types";
import { assertValidClaim } from "util/typeUtils";
import { fineos, fineosPages, portal } from "../../../actions";
import { config } from "../../../actions/common";
import { describeIf, getTwilioNumber, itIf } from "../../../util";
import { add, format } from "date-fns";
import faker from "faker";

describeIf(
  config("MFA_ENABLED") === "true",
  "Claimant Registration with MFA",
  {},
  () => {
    const primary = getTwilioNumber(0);
    const secondary = getTwilioNumber(1);

    itIf(
      config("HAS_CHANNEL_SWITCHING") === "true",
      "As a CCR, I should be able to submit a continuous bonding application through FINEOS",
      {},
      () => {
        fineos.before();
        cy.task("generateClaim", "BCAP90").then((claim) => {
          cy.stash("claimantPhoneNumber", primary);
          cy.stash("claim", claim);
          assertValidClaim(claim.claim);
          const customer = fineosPages.ClaimantPage.visit(
            claim.claim.tax_identifier
          );
          // const customer = fineosPages.ClaimantPage.visit("005-46-5314")
          customer.editPersonalIdentification(
            {
              date_of_birth: format(
                faker.date.between(
                  add(new Date(), { years: -65 }),
                  add(new Date(), { years: -18 })
                ),
                "MM/dd/yyyy"
              ),
            },
            config("HAS_APRIL_UPGRADE") === "true" ? true : false
          );
          customer.setPhoneNumber(primary);
          customer.createNotification(claim.claim).then((fineos_absence_id) => {
            cy.log(fineos_absence_id);
            cy.stash("submission", {
              fineos_absence_id: fineos_absence_id,
              timestamp_from: Date.now(),
            });
          });
        });
      }
    );

    it("As a newly-registered claimant, I should be able to decline setting up MFA", () => {
      portal.before();
      cy.task("generateCredentials").then((credentials) => {
        cy.stash("credentials", credentials);
        portal.registerAsClaimant(credentials);
        portal.loginClaimant(credentials);
        portal.assertLoggedIn();
        portal.consentDataSharing();
        portal.declineMFA();

        if (config("HAS_CHANNEL_SWITCHING") === "true") {
          cy.unstash<DehydratedClaim>("claim").then((claim) => {
            cy.unstash<Submission>("submission").then((submission) => {
              if (!claim.claim.tax_identifier) {
                throw new Error(
                  `Employee SSN missing for scenario: ${claim.scenario}`
                );
              }
              portal.resumeFineosApplication(
                claim.claim.tax_identifier,
                submission.fineos_absence_id
              );
              portal.assertClaimImportError("Your login is not verified.");
            });
          });
        }
      });
    });

    const registerMfa =
      it("As claimant who's declined to set up MFA, I should be able to enable MFA", () => {
        portal.before();
        cy.unstash<Credentials>("credentials").then((credentials) => {
          portal.loginClaimant(credentials);
          portal.assertLoggedIn();
          portal.enableMFA(primary);
          portal.logout();
          portal.loginMFA(credentials, primary);

          if (config("HAS_CHANNEL_SWITCHING") === "true") {
            cy.unstash<DehydratedClaim>("claim").then((claim) => {
              cy.unstash<Submission>("submission").then((submission) => {
                if (!claim.claim.tax_identifier) {
                  throw new Error(
                    `Employee SSN missing for scenario: ${claim.scenario}`
                  );
                }
                portal.resumeFineosApplication(
                  claim.claim.tax_identifier,
                  submission.fineos_absence_id
                );
                portal.assertClaimImportSuccess(submission.fineos_absence_id);
                cy.contains("a", "Continue application").click();
                cy.contains("h1", "Your in-progress application");
              });
            });
          }
        });
      });

    const updateMfa =
      it("As a user w/MFA enabled, I should be able to update my MFA phone number successfully", () => {
        cy.dependsOnPreviousPass([registerMfa]);
        portal.before();
        cy.unstash<Credentials>("credentials").then((credentials) => {
          portal.loginMFA(credentials, primary);
          portal.updateNumberMFA(secondary);
          portal.logout();
          portal.loginMFA(credentials, secondary);
        });
      });

    it("As a user w/MFA enabled, I should be able to successfully disable my MFA phone number", () => {
      cy.dependsOnPreviousPass([registerMfa, updateMfa]);
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
