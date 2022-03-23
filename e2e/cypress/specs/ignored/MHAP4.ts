import { portal, fineos, fineosPages } from "../../actions";
import { Submission } from "../../../src/types";
import { assertValidClaim } from "../../../src/util/typeUtils";
import { getDocumentReviewTaskName } from "../../../src/util/documents";
import { config } from "../../actions/common";

describe("Submitting a Medical pregnancy claim and adding bonding leave in Fineos", () => {
  it("Create a financially eligible claim (MHAP4) in which an employer will respond", () => {
    portal.before();

    cy.task("generateClaim", "MHAP4").then((claim) => {
      cy.task("submitClaimToAPI", claim).then((response) => {
        cy.stash("submission", {
          application_id: response.application_id,
          fineos_absence_id: response.fineos_absence_id,
          timestamp_from: Date.now(),
        });
        // Complete Employer Response
        assertValidClaim(claim.claim);

        portal.loginLeaveAdmin(claim.claim.employer_fein);
        portal.visitActionRequiredERFormPage(response.fineos_absence_id);
        portal.respondToLeaveAdminRequest(false, true, true);
      });
    });
    cy.wait(1000);
  });

  // Check for ER and approval claim in Fineos
  it("In Fineos, complete an Adjudication Approval along w/adding Bonding Leave", () => {
    fineos.before();
    cy.unstash<Submission>("submission").then(({ fineos_absence_id }) => {
      cy.unstash<DehydratedClaim>("claim").then((claim) => {
        const claimPage = fineosPages.ClaimPage.visit(fineos_absence_id)
          .tasks((tasks) => {
            claim.documents.forEach((doc) =>
              tasks.assertTaskExists(
                getDocumentReviewTaskName(doc.document_type)
              )
            );
          })
          .shouldHaveStatus("Applicability", "Applicable")
          .shouldHaveStatus("Eligibility", "Met")
          .adjudicate((adjudication) => {
            adjudication
              .evidence((evidence) =>
                claim.documents.forEach((doc) =>
                  evidence.receive(doc.document_type)
                )
              )
              .certificationPeriods((certPreiods) => certPreiods.prefill())
              .acceptLeavePlan();
          });
        claimPage.approve("Approved", config("HAS_APRIL_UPGRADE") === "true");
        fineos.addBondingLeaveFlow(new Date());
      });
    });
  });
});
