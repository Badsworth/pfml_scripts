import { extractLeavePeriod } from "../../../../src/util/claims";
import { portal, fineos, fineosPages } from "../../../actions";
import { Submission } from "../../../../src/types";
import { assertValidClaim } from "../../../../src/util/typeUtils";
import { addBusinessDays, addWeeks } from "date-fns";
import { config } from "../../../actions/common";

describe("Submit medical application via the web portal: Adjudication Approval & payment checking", () => {
  const submissionTest =
    it("As a claimant, I should be able to submit a reduced medical application through the portal", () => {
      portal.before();
      cy.task("generateClaim", "MRAP30").then((claim) => {
        cy.stash("claim", claim);
        const application: ApplicationRequestBody = claim.claim;
        const paymentPreference = claim.paymentPreference;

        portal.loginClaimant();
        portal.skipLoadingClaimantApplications();

        // Submit Claim
        portal.startClaim();
        portal.submitClaimPartOne(application, false);
        portal.waitForClaimSubmission().then((data) => {
          cy.stash("submission", {
            application_id: data.application_id,
            fineos_absence_id: data.fineos_absence_id,
            timestamp_from: Date.now(),
          });
        });
        portal.submitClaimPartsTwoThree(
          application,
          paymentPreference,
          claim.is_withholding_tax
        );
      });
    });

  const erApproval =
    it("Leave admin will submit ER approval for employee", () => {
      cy.dependsOnPreviousPass([submissionTest]);
      portal.before();
      cy.unstash<DehydratedClaim>("claim").then((claim) => {
        cy.unstash<Submission>("submission").then((submission) => {
          assertValidClaim(claim.claim);
          portal.loginLeaveAdmin(claim.claim.employer_fein);
          portal.selectClaimFromEmployerDashboard(submission.fineos_absence_id);
          portal.visitActionRequiredERFormPage(submission.fineos_absence_id);
          portal.respondToLeaveAdminRequest(false, true, true);
        });
      });
    });

  const approval =
    it("CSR rep will approve reduced medical application", () => {
      cy.dependsOnPreviousPass([erApproval]);
      fineos.before();
      cy.unstash<DehydratedClaim>("claim").then((claim) => {
        cy.unstash<Submission>("submission").then((submission) => {
          cy.tryCount().then((tryCount) => {
            const claimPage = fineosPages.ClaimPage.visit(
              submission.fineos_absence_id
            );
            if (tryCount > 0) {
              fineos.assertClaimStatus("Approved");
              claimPage.triggerNotice("Designation Notice");
              return;
            }
            claimPage.adjudicate((adjudication) => {
              adjudication.evidence((evidence) => {
                // Receive all of the claim documentation.
                claim.documents.forEach((document) => {
                  evidence.receive(document.document_type);
                });
              });
              adjudication.certificationPeriods((cert) => cert.prefill());
              adjudication.acceptLeavePlan();
            });
            claimPage.shouldHaveStatus("Applicability", "Applicable");
            claimPage.shouldHaveStatus("Eligibility", "Met");
            claimPage.shouldHaveStatus("Evidence", "Satisfied");
            claimPage.shouldHaveStatus("Availability", "Time Available");
            claimPage.shouldHaveStatus("Restriction", "Passed");
            claimPage.shouldHaveStatus("PlanDecision", "Accepted");
            claimPage.approve(
              "Approved",
              config("HAS_APRIL_UPGRADE") === "true"
            );
            claimPage.triggerNotice("Designation Notice");
          });
        });
      });
    });

  it(
    "Should be able to confirm the weekly payment amount for a reduced schedule",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass([approval]);
      fineos.before();
      cy.unstash<DehydratedClaim>("claim").then((claim) => {
        cy.unstash<Submission>("submission").then((submission) => {
          const payment = claim.metadata
            ?.expected_weekly_payment as unknown as number;
          fineosPages.ClaimPage.visit(submission.fineos_absence_id).paidLeave(
            (leaveCase) => {
              leaveCase
                .assertAmountsPending([{ net_payment_amount: payment }])
                .assertMatchingPaymentDates();
            }
          );
        });
      });
    }
  );

  it("Should display a checkback date of (leave start date + 2 weeks + 3 business days) on the payment status page", () => {
    cy.dependsOnPreviousPass([approval]);
    portal.before();
    portal.loginClaimant();
    cy.unstash<DehydratedClaim>("claim").then((claim) => {
      cy.unstash<Submission>("submission").then((submission) => {
        const [start] = extractLeavePeriod(
          {
            leave_details: claim.claim.leave_details,
          },
          "reduced_schedule_leave_periods"
        );
        if (!claim.claim.leave_details?.reason)
          throw Error("Leave reason undefined on unstashed claim object");
        portal.claimantGoToClaimStatus(submission.fineos_absence_id);
        portal.claimantAssertClaimStatus([
          {
            leave: claim.claim.leave_details?.reason,
            status: "Approved",
          },
        ]);
        portal.viewPaymentStatus();
        const twoWeeksAfterStart = addWeeks(start, 2);
        // @todo: Once https://lwd.atlassian.net/browse/PORTAL-2003 is rolled out to all lower environments the LOC below should be used:
        // portal.assertPaymentCheckBackDate(addBusinessDays(twoWeeksAfterStart, 4))
        portal.assertPaymentCheckBackDate(undefined, [
          addBusinessDays(twoWeeksAfterStart, 3),
          addBusinessDays(twoWeeksAfterStart, 4),
        ]);
      });
    });
  });
});
