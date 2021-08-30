import { fineos, fineosPages } from "../../../actions";
import { getFineosBaseUrl } from "../../../config";
import { Submission } from "../../../../src/types";
import { getSubmissionFromApiResponse } from "../../../../src/util/claims";
import { FineosSecurityGroups } from "../../../../src/submission/fineos.pages";

const SECURITY_GROUP: FineosSecurityGroups = "SaviLinx Agents (sec)";
const permissions: Record<FineosSecurityGroups, boolean> = {
  "DFML Claims Examiners(sec)": true,
  "DFML Claims Supervisors(sec)": true,
  "DFML Compliance Analyst(sec)": true,
  "DFML Compliance Supervisors(sec)": true,
  "DFML Appeals Administrator(sec)": true,
  "DFML Appeals Examiner I(sec)": false,
  "DFML Appeals Examiner II(sec)": false,
  "SaviLinx Agents (sec)": false,
  "SaviLinx Secured Agents(sec)": false,
  "SaviLinx Supervisors(sec)": true,
  "DFML IT(sec)": false,
  "Post-Prod Admin(sec)": false,
};

describe("Supress correspondence secure actions", () => {
  const submission = it(
    "Given a submitted claim",
    { baseUrl: getFineosBaseUrl() },
    () => {
      fineos.before();
      cy.visit("/");
      //Submit a claim via the API, including Employer Response.
      cy.task("generateClaim", "CHAP_ER").then((claim) => {
        cy.stash("claim", claim);
        cy.task("submitClaimToAPI", claim).then((response) => {
          cy.stash("submission", getSubmissionFromApiResponse(response));
        });
      });
    }
  );
  it(
    `${SECURITY_GROUP} ${
      permissions[SECURITY_GROUP] ? "can" : "cannot"
    } suppress notifications`,
    { baseUrl: getFineosBaseUrl() },
    () => {
      cy.dependsOnPreviousPass([submission]);
      cy.unstash<DehydratedClaim>("claim").then((claim) => {
        cy.unstash<Submission>("submission").then(
          ({ application_id, fineos_absence_id }) => {
            fineos.before();
            cy.visit("/");
            cy.stash("claim", claim.claim);
            cy.stash("submission", {
              application_id: application_id,
              fineos_absence_id: fineos_absence_id,
              timestamp_from: Date.now(),
            });
            fineosPages.ClaimPage.visit(
              fineos_absence_id
            ).suppressCorrespondence(permissions[SECURITY_GROUP]);
          }
        );
      });
    }
  );
});
