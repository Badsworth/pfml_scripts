import { fineos, fineosPages } from "../../../actions";
import { getFineosBaseUrl } from "../../../config";
import { Submission } from "../../../../src/types";
import { getSubmissionFromApiResponse } from "../../../../src/util/claims";
import { FineosSecurityGroups } from "../../../../src/submission/fineos.pages";
import { config } from "../../../actions/common";

const permissions: [FineosSecurityGroups, boolean][] = [
  ["DFML Claims Examiners(sec)", true],
  ["DFML Claims Supervisors(sec)", true],
  ["DFML Compliance Analyst(sec)", true],
  ["DFML Compliance Supervisors(sec)", true],
  ["DFML Appeals Administrator(sec)", true],
  ["DFML Appeals Examiner I(sec)", false],
  ["DFML Appeals Examiner II(sec)", false],
  ["SaviLinx Agents (sec)", false],
  ["SaviLinx Secured Agents(sec)", false],
  ["SaviLinx Supervisors(sec)", true],
  ["DFML IT(sec)", false],
  ["Post-Prod Admin(sec)", false],
];
// Set baseurl
Cypress.config("baseUrl", getFineosBaseUrl());

const ssoAccount2Credentials: Credentials = {
  username: config("SSO2_USERNAME"),
  password: config("SSO2_PASSWORD"),
};

permissions.forEach(([securityGroup, canUseSecureAction]) => {
  describe("Supress correspondence secure actions", () => {
    const submission = it("Given a submitted claim", () => {
      //Submit a claim via the API, including Employer Response.
      cy.task("generateClaim", "CHAP_ER").then((claim) => {
        cy.stash("claim", claim);
        cy.task("submitClaimToAPI", claim).then((response) => {
          cy.stash("submission", getSubmissionFromApiResponse(response));
          // Set the security group for second sso account.
          cy.task("chooseFineosRole", {
            userId: ssoAccount2Credentials.username,
            preset: securityGroup,
          });
        });
      });
    });
    it(`${securityGroup} ${
      canUseSecureAction ? "can" : "cannot"
    } suppress notifications`, () => {
      cy.dependsOnPreviousPass([submission]);
      cy.unstash<DehydratedClaim>("claim").then((claim) => {
        cy.unstash<Submission>("submission").then(
          ({ application_id, fineos_absence_id }) => {
            fineos.before(ssoAccount2Credentials);
            cy.visit("/");
            cy.stash("claim", claim.claim);
            cy.stash("submission", {
              application_id: application_id,
              fineos_absence_id: fineos_absence_id,
              timestamp_from: Date.now(),
            });
            fineosPages.ClaimPage.visit(
              fineos_absence_id
            ).suppressCorrespondence(canUseSecureAction);
          }
        );
      });
    });
  });
});
