import { fineos, fineosPages } from "../../../actions";
import { FineosSecurityGroups } from "../../../../src/submission/fineos.pages";
import { assertValidClaim } from "../../../../src/util/typeUtils";
import { config } from "../../../actions/common";

const userTypes: {
  security_group: FineosSecurityGroups;
  can_add_case: boolean;
}[] = [
  {
    security_group: "DFML Claims Examiners(sec)",
    can_add_case: true,
  },
  {
    security_group: "DFML Claims Supervisors(sec)",
    can_add_case: true,
  },
  {
    security_group: "DFML Compliance Analyst(sec)",
    can_add_case: false,
  },
  {
    security_group: "DFML Compliance Supervisors(sec)",
    can_add_case: true,
  },
  {
    security_group: "DFML Appeals Administrator(sec)",
    can_add_case: true,
  },
  {
    security_group: "DFML Appeals Examiner I(sec)",
    can_add_case: true,
  },
  {
    security_group: "DFML Appeals Examiner II(sec)",
    can_add_case: true,
  },
  {
    security_group: "SaviLinx Agents (sec)",
    can_add_case: false,
  },
  {
    security_group: "SaviLinx Secured Agents(sec)",
    can_add_case: false,
  },
  {
    security_group: "SaviLinx Supervisors(sec)",
    can_add_case: false,
  },
  {
    security_group: "DFML IT(sec)",
    can_add_case: false,
  },
];

describe("Historical absence secure actions", () => {
  userTypes.forEach((userType) => {
    describe(`${userType.security_group}:`, () => {
      before(() => {
        cy.task("chooseFineosRole", {
          userId: config("SSO2_USERNAME"),
          preset: userType.security_group,
        });
      });
      it(`${userType.security_group} ${
        userType.can_add_case ? "can" : "can't"
      } add case on intake`, () => {
        fineos.before({
          username: config("SSO2_USERNAME"),
          password: config("SSO2_PASSWORD"),
        });
        //Submit a claim via the API, including Employer Response.
        cy.task("generateClaim", "CHAP_ER").then((claim) => {
          assertValidClaim(claim.claim);
          // Create historical absence
          fineosPages.ClaimantPage.visit(claim.claim.tax_identifier);
          cy.get(
            `div[id^="MENUBAR.PartySubjectMenu_"][id$="_MENUBAR.PartySubjectMenu"] div[title="Add Case"]`
          ).should(userType.can_add_case ? "be.visible" : "not.be.visible");
        });
      });
    });
  });
});
