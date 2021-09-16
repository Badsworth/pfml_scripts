import { fineos, fineosPages } from "../../../actions";
import { FineosSecurityGroups } from "../../../../src/submission/fineos.pages";
import { assertValidClaim } from "../../../../src/util/typeUtils";
import { Submission } from "../../../../src/types";
import { getSubmissionFromApiResponse } from "../../../../src/util/claims";
import { config } from "../../../actions/common";

const securityGroups: [FineosSecurityGroups, boolean][] = [
  ["DFML Claims Examiners(sec)", false],
  ["DFML Claims Supervisors(sec)", true],
  ["DFML Compliance Analyst(sec)", false],
  ["DFML Compliance Supervisors(sec)", true],
  ["DFML Appeals Administrator(sec)", true],
  ["DFML Appeals Examiner I(sec)", false],
  ["DFML Appeals Examiner II(sec)", false],
  ["SaviLinx Agents (sec)", false],
  ["SaviLinx Secured Agents(sec)", false],
  ["SaviLinx Supervisors(sec)", true],
  ["DFML IT(sec)", false],
];
securityGroups.forEach(([group, canChangeDocType]) => {
  describe(`${group} ${
    canChangeDocType ? "can" : "can't"
  } change the document type for`, () => {
    describe("Documents uploaded manually through Fineos UI", () => {
      const submit = it("Given a submitted claim", () => {
        fineos.before();
        cy.task("chooseFineosRole", {
          userId: config("SSO2_USERNAME"),
          preset: group,
        });
        //Submit a claim via the Fineos.
        cy.task("generateClaim", "CHAP_ER").then((claim) => {
          assertValidClaim(claim.claim);
          cy.stash("claim", claim);
          fineosPages.ClaimantPage.visit(claim.claim.tax_identifier)
            .createNotification(claim.claim)
            .then((fineos_absence_id) => {
              cy.stash("submission", { fineos_absence_id });
              fineosPages.ClaimPage.visit(fineos_absence_id).documents(
                (docPage) => {
                  claim.documents.forEach((doc) =>
                    docPage.uploadDocument(doc.document_type)
                  );
                }
              );
            });
        });
      });
      it(`${group} ${
        canChangeDocType ? "can" : "can't"
      } change the document type`, () => {
        cy.dependsOnPreviousPass([submit]);
        // Login as a second account and try to change the doc type
        fineos.before({
          username: config("SSO2_USERNAME"),
          password: config("SSO2_PASSWORD"),
        });
        cy.unstash<Submission>("submission").then(({ fineos_absence_id }) => {
          fineosPages.ClaimPage.visit(fineos_absence_id).documents(
            (docPage) => {
              docPage.changeDocType(
                "Identification Proof",
                // "State managed Paid Leave Confirmation" doc type may be deprecated in the near future, change to another type from the same folder if needed
                "State managed Paid Leave Confirmation",
                canChangeDocType
              );
            }
          );
        });
      });
    });

    describe("Documents uploaded via portal", () => {
      const apiSubmit = it("Given a submitted claim", () => {
        cy.task("generateClaim", "CHAP_ER").then((claim) => {
          cy.stash("claim", claim);
          cy.task("submitClaimToAPI", claim).then((res) =>
            cy.stash("submission", getSubmissionFromApiResponse(res))
          );
        });
      });

      it(`${group} ${
        canChangeDocType ? "can" : "can't"
      } change the document type`, () => {
        cy.dependsOnPreviousPass([apiSubmit]);
        // Login as a second account and try to change the doc type
        fineos.before({
          username: config("SSO2_USERNAME"),
          password: config("SSO2_PASSWORD"),
        });
        cy.unstash<DehydratedClaim>("claim").then(() => {
          cy.unstash<Submission>("submission").then(({ fineos_absence_id }) => {
            fineosPages.ClaimPage.visit(fineos_absence_id).documents((docs) => {
              docs.changeDocType(
                "Identification Proof",
                // "State managed Paid Leave Confirmation" doc type may be deprecated in the near future, change to another type from the same folder if needed
                "State managed Paid Leave Confirmation",
                canChangeDocType
              );
            });
          });
        });
      });
    });
  });
});
