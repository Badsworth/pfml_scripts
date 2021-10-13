import { fineos, fineosPages } from "../../../actions";
import { FineosSecurityGroups } from "../../../../src/submission/fineos.pages";
import { getFineosBaseUrl } from "../../../config";
import { config } from "../../../actions/common";
import { waitForAjaxComplete } from "../../../actions/fineos";

const userPermissions: {
  security_group: FineosSecurityGroups;
  employer_complete: boolean;
  employer_remove: boolean;
  employer_suppress: boolean;
  employer_reopen: boolean;
}[] = [
  {
    security_group: "DFML Claims Examiners(sec)",
    employer_complete: true,
    employer_remove: true,
    employer_suppress: true,
    employer_reopen: true,
  },
  {
    security_group: "DFML Claims Supervisors(sec)",
    employer_complete: true,
    employer_remove: true,
    employer_suppress: true,
    employer_reopen: true,
  },
  {
    security_group: "DFML Compliance Analyst(sec)",
    employer_complete: true,
    employer_remove: true,
    employer_suppress: true,
    employer_reopen: true,
  },
  {
    security_group: "DFML Compliance Supervisors(sec)",
    employer_complete: true,
    employer_remove: true,
    employer_suppress: true,
    employer_reopen: true,
  },
  {
    security_group: "DFML Appeals Administrator(sec)",
    employer_complete: true,
    employer_remove: true,
    employer_suppress: true,
    employer_reopen: true,
  },
  {
    security_group: "DFML Appeals Examiner I(sec)",
    employer_complete: true,
    employer_remove: true,
    employer_suppress: true,
    employer_reopen: true,
  },
  {
    security_group: "DFML Appeals Examiner II(sec)",
    employer_complete: true,
    employer_remove: true,
    employer_suppress: true,
    employer_reopen: true,
  },
  {
    security_group: "SaviLinx Agents (sec)",
    employer_complete: false,
    employer_remove: false,
    employer_suppress: false,
    employer_reopen: false,
  },
  {
    security_group: "SaviLinx Secured Agents(sec)",
    employer_complete: false,
    employer_remove: false,
    employer_suppress: false,
    employer_reopen: false,
  },
  {
    security_group: "SaviLinx Supervisors(sec)",
    employer_complete: false,
    employer_remove: false,
    employer_suppress: false,
    employer_reopen: false,
  },
  {
    security_group: "DFML IT(sec)",
    employer_complete: true,
    employer_remove: true,
    employer_suppress: true,
    employer_reopen: true,
  },
];
// Set baseurl
Cypress.config("baseUrl", getFineosBaseUrl());

const ssoAccount2Credentials: Credentials = {
  username: config("SSO2_USERNAME"),
  password: config("SSO2_PASSWORD"),
};

//`${userPermission.security_group}:`

describe("Check the O/R is accessible to modify with secure actions", () => {
  userPermissions.forEach((userPermission) => {
    it(`${userPermission.security_group} checking the outstanding requirement access`, () => {
      describe(`${userPermission.security_group}:`, () => {
        before((done) => {
          cy.task("chooseFineosRole", {
            userId: ssoAccount2Credentials.username,
            preset: userPermission.security_group,
            debug: false,
          }).then(done);
        })
      })
    });
    it(`${userPermission.security_group} ${
      userPermission.employer_complete ? "can" : "can't"
    } complete, remove, or suppress available in O/R`, () => {
      fineos.before(ssoAccount2Credentials);
      cy.task("generateClaim", "WDCLAIM").then((claim) => {
        cy.task("submitClaimToAPI", claim).then((response) => {
          const claimPage = fineosPages.ClaimPage.visit(response.fineos_absence_id);
          claimPage.adjudicate((adjudicate) => {
            adjudicate.evidence((evidence) => {
              claim.documents.forEach((docs) => {
                evidence.receive(docs.document_type);
              });
            });
          });
          // Check the Complete, Suppress, and Remove for each secure group
          claimPage.outstandingRequirements((outstanding_requirement) => {
            outstanding_requirement.complete("Received", "Complete Employer Confirmation", userPermission.employer_complete)
            waitForAjaxComplete()
            cy.screenshot(`${response.fineos_absence_id} - ${userPermission.security_group} showing access to complete is ${userPermission.employer_complete}`)
            outstanding_requirement.reopen(userPermission.employer_reopen)
            waitForAjaxComplete()
            outstanding_requirement.suppress("Auto-Suppressed", "Suppress Employer Confirmation", userPermission.employer_suppress)
            cy.screenshot(`${response.fineos_absence_id} - ${userPermission.security_group} showing access to suppress is ${userPermission.employer_suppress}`)
            waitForAjaxComplete()
            outstanding_requirement.reopen(userPermission.employer_reopen)
            waitForAjaxComplete()
            outstanding_requirement.removeOR(userPermission.employer_remove)
            waitForAjaxComplete()
            cy.screenshot(`${response.fineos_absence_id} - ${userPermission.security_group} showing access to remove is ${userPermission.employer_remove}`)
          });
          }
        );
      })
    });
  });
});

