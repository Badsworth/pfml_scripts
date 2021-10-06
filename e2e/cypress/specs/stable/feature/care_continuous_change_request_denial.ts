import { fineos, fineosPages, portal } from "../../../actions";
import { Submission } from "../../../../src/types";
import { extractLeavePeriod } from "../../../../src/util/claims";
import { addDays, format } from "date-fns";
describe("Post-approval (notifications/notices)", () => {
  const approval =
    it("Submit a Care for a Family member claim for approval", () => {
      fineos.before();
      //Submit a claim via the API, including Employer Response.
      cy.task("generateClaim", "CHAP_ER").then((claim) => {
        cy.stash("claim", claim);
        cy.task("submitClaimToAPI", claim).then((response) => {
          if (!response.fineos_absence_id) {
            throw new Error("Response contained no fineos_absence_id property");
          }
          const [startDate, endDate] = extractLeavePeriod(claim.claim);
          const newStartDate = format(
            addDays(new Date(startDate), 2),
            "MM/dd/yyyy"
          );
          const newEndDate = format(
            addDays(new Date(endDate), 2),
            "MM/dd/yyyy"
          );
          const submission: Submission = {
            application_id: response.application_id,
            fineos_absence_id: response.fineos_absence_id,
            timestamp_from: Date.now(),
          };

          cy.stash("extendedDates", [newStartDate, newEndDate]);
          cy.stash("submission", submission);
          // Approve the claim
          fineosPages.ClaimPage.visit(response.fineos_absence_id)
            .adjudicate((adjudication) => {
              adjudication
                .evidence((evidence) => {
                  claim.documents.forEach((doc) =>
                    evidence.receive(doc.document_type)
                  );
                })
                .certificationPeriods((cert) => cert.prefill())
                .acceptLeavePlan();
            })
            // Skip checking tasks. We do that in other tests.
            // Also skip checking claim status for the same reason.
            .approve()
            .triggerNotice("Preliminary Designation");
        });
      });
    });

  const denyModification =
    it('Generates a "Denial" document for extend time which will be "Change Request Denial"', () => {
      cy.dependsOnPreviousPass([approval]);
      fineos.before();
      cy.unstash<Submission>("submission").then((submission) => {
        cy.unstash<[string, string]>("extendedDates").then(
          ([startDate, endDate]) => {
            //visit claim after approval for extended leave with denial.
            const claimPage = fineosPages.ClaimPage.visit(
              submission.fineos_absence_id
            ).benefitsExtension((benefitsExtension) =>
              benefitsExtension.extendLeave(startDate, endDate)
            );
            claimPage.leaveDetails((leaveDetails) => {
              leaveDetails.rejectSelectPlan();
            });
            claimPage
              .denyExtendedTime("Claimant/Family member deceased")
              .triggerNotice("Leave Request Declined")
              .documents((docPage) =>
                docPage.assertDocumentExists("Denial Notice")
              );
          }
        );
      });
    });

  it("Displays proper statuses in the claimant portal", () => {
    cy.dependsOnPreviousPass([denyModification]);
    portal.before({
      claimantShowStatusPage: true,
    });
    cy.visit("/");
    portal.loginClaimant();
    cy.unstash<Submission>("submission").then((submission) => {
      // Wait for the legal document to arrive.
      portal.claimantGoToClaimStatus(submission.fineos_absence_id);
      portal.claimantAssertClaimStatus([
        { leave: "Care for a Family Member", status: "Denied" },
      ]);
      cy.findByText("Denial notice (PDF)")
        .should("be.visible")
        .click({ force: true });
      portal.downloadLegalNotice(submission.fineos_absence_id);
    });
  });
});
