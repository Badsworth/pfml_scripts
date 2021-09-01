import { FineosSecurityGroups } from "../../../../src/submission/fineos.pages";
import { fineos, fineosPages } from "../../../actions";
import { config } from "../../../actions/common";
import { assertValidClaim } from "util/typeUtils";

const SECURITY_GROUP: FineosSecurityGroups = "SaviLinx Agents (sec)";
const permissions: Record<FineosSecurityGroups, boolean> = {
  "DFML Claims Examiners(sec)": true,
  "DFML Claims Supervisors(sec)": true,
  "DFML Compliance Analyst(sec)": true,
  "DFML Compliance Supervisors(sec)": true,
  "DFML Appeals Administrator(sec)": false,
  "DFML Appeals Examiner I(sec)": false,
  "DFML Appeals Examiner II(sec)": false,
  "SaviLinx Agents (sec)": false,
  "SaviLinx Secured Agents(sec)": false,
  "SaviLinx Supervisors(sec)": false,
  "DFML IT(sec)": false,
  "Post-Prod Admin(sec)": false,
};

describe("Supress correspondence secure actions", () => {
  const credentials: Credentials = {
    username: config("PORTAL_USERNAME"),
    password: config("PORTAL_PASSWORD"),
  };

  let ssn: string;
  const approval = it("Given a fully approved claim", () => {
    fineos.before();
    // Submit a claim via the API, including Employer Response.
    cy.task("generateClaim", "REDUCED_ER").then((claim) => {
      cy.stash("claim", claim.claim);
      cy.task("submitClaimToAPI", {
        ...claim,
        credentials,
      }).then(() => {
        assertValidClaim(claim.claim);
        ssn = claim.claim.tax_identifier;
      });
    });
  });

  it(`${SECURITY_GROUP} ${
    permissions[SECURITY_GROUP] ? "can" : "cannot"
  } suppress notifications`, () => {
    cy.dependsOnPreviousPass([approval]);
    fineos.before();
    // @todo: create claimant in all envs for this test
    fineosPages.ClaimantPage.visit(ssn)
      .paymentPreferences()
      .edit()
      .checkBulkPayee(permissions[SECURITY_GROUP]);
    cy.screenshot();
  });
});
