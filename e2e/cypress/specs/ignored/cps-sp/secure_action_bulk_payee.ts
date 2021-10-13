import { FineosSecurityGroups } from "../../../../src/submission/fineos.pages";
import { fineos, fineosPages } from "../../../actions";
import { assertValidClaim } from "util/typeUtils";
import { config } from "../../../actions/common";

const permissions: [FineosSecurityGroups, boolean][] = [
  ["DFML Claims Examiners(sec)", true],
  ["DFML Claims Supervisors(sec)", true],
  ["DFML Compliance Analyst(sec)", true],
  ["DFML Compliance Supervisors(sec)", true],
  ["DFML Appeals Administrator(sec)", false],
  ["DFML Appeals Examiner I(sec)", false],
  ["DFML Appeals Examiner II(sec)", false],
  ["SaviLinx Agents (sec)", false],
  ["SaviLinx Secured Agents(sec)", false],
  ["SaviLinx Supervisors(sec)", false],
  ["DFML IT(sec)", false],
  ["Post-Prod Admin(sec)", false],
];

const ssoAccount2Credentials: Credentials = {
  username: config("SSO2_USERNAME"),
  password: config("SSO2_PASSWORD"),
};

permissions.forEach(([userSecurityGroup, canChangeDocType]) => {
  describe("Suppress correspondence secure actions", () => {
    let ssn: string;
    const approval = it("Given a fully approved claim", () => {
      // Submit a claim via the API, including Employer Response.
      cy.task("generateClaim", "REDUCED_ER").then((claim) => {
        cy.stash("claim", claim.claim);
        cy.task("submitClaimToAPI", claim).then(() => {
          assertValidClaim(claim.claim);
          ssn = claim.claim.tax_identifier;
          cy.task("chooseFineosRole", {
            userId: ssoAccount2Credentials.username,
            preset: userSecurityGroup,
            debug: false,
          });
        });
      });
    });

    it(`${userSecurityGroup} ${
      canChangeDocType ? "can" : "cannot"
    } suppress notifications`, () => {
      cy.dependsOnPreviousPass([approval]);
      fineos.before(ssoAccount2Credentials);
      fineosPages.ClaimantPage.visit(ssn)
        .paymentPreferences()
        .edit()
        .checkBulkPayee(canChangeDocType);
      cy.screenshot();
    });
  });
});
