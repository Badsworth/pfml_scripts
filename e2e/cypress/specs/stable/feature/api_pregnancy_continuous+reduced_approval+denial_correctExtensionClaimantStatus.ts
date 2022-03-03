import { fineos, fineosPages, portal } from "../../../actions";
import { Submission } from "../../../../src/types";
import { addMonths, addDays, format } from "date-fns";
import { extractLeavePeriod } from "../../../../src/util/claims";
import { config } from "../../../actions/common";

describe("Submit medical pre-birth application via the web portal", () => {
  const submission =
    it("Submits a Medical/Pregnancy claim through the API", () => {
      cy.task("generateClaim", "PREBIRTH").then((claim) => {
        cy.task("submitClaimToAPI", claim).then((submission) => {
          cy.stash("claim", claim);
          cy.stash("submission", {
            application_id: submission.application_id,
            fineos_absence_id: submission.fineos_absence_id,
            timestamp_from: Date.now(),
          });
        });
      });
    });

  const approval = it(
    "CSR rep will approve reduced medical application",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass([submission]);
      fineos.before();
      cy.unstash<DehydratedClaim>("claim").then((claim) => {
        cy.unstash<Submission>("submission").then((submission) => {
          const claimPage = fineosPages.ClaimPage.visit(
            submission.fineos_absence_id
          );
          claimPage.triggerNotice("Preliminary Designation");
          fineos.onTab("Absence Hub");
          claimPage
            .adjudicate((adjudication) => {
              adjudication
                .evidence((evidence) => {
                  // Receive all of the claim documentation.
                  claim.documents.forEach((document) => {
                    evidence.receive(document.document_type);
                  });
                })
                .certificationPeriods((cert) => cert.prefill())
                .acceptLeavePlan();
            })
            .shouldHaveStatus("Applicability", "Applicable")
            .shouldHaveStatus("Eligibility", "Met")
            .shouldHaveStatus("Evidence", "Satisfied")
            .shouldHaveStatus("Availability", "Time Available")
            .shouldHaveStatus("Restriction", "Passed")
            .shouldHaveStatus("PlanDecision", "Accepted")
            .approve();
        });
      });
    }
  );
  const extension = it(
    "CSR rep will add bonding leave to the absence case",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass([approval]);
      fineos.before();
      cy.unstash<Submission>("submission").then((submission) => {
        fineosPages.ClaimPage.visit(submission.fineos_absence_id)
          .benefitsExtension((benefitsExtension) => {
            const startDate = addMonths(new Date(), 2);
            const startDateFormatted = format(startDate, "MM/dd/yyyy");
            const endDateFormatted = format(
              addDays(startDate, 2),
              "MM/dd/yyyy"
            );
            cy.stash("extensionDates", [startDateFormatted, endDateFormatted]);
            benefitsExtension.extendLeave(
              startDateFormatted,
              endDateFormatted,
              true,
              "reduced"
            );
          })
          .outstandingRequirements((outstandingRequirements) =>
            outstandingRequirements.add()
          );
      });
    }
  );

  it("Will display the approprite claimant statuses in the leave admin portal", () => {
    cy.dependsOnPreviousPass([extension]);
    portal.before();
    cy.unstash<Submission>("submission").then((submission) => {
      cy.unstash<DehydratedClaim>("claim").then((claim) => {
        cy.unstash<[string, string]>("extensionDates").then(
          (extensionDates) => {
            if (!claim.claim.employer_fein)
              throw Error(
                "Property 'employer_fein' undefined in unstashed claim"
              );
            portal.loginLeaveAdmin(claim.claim.employer_fein);
            portal.visitActionRequiredERFormPage(submission.fineos_absence_id);
            const [start, end] = extractLeavePeriod(claim.claim);
            portal.leaveAdminAssertClaimStatus([
              {
                leave: "Serious Health Condition - Employee",
                status: "Approved",
                leavePeriods: [start.toISOString(), end.toISOString()],
              },
              {
                leave: "Child Bonding",
                status: "Pending",
                leavePeriods: extensionDates,
              },
            ]);
            portal.respondToLeaveAdminRequest(false, true, true);
          }
        );
      });
    });
  });

  const denyExtension = it(
    "CSR rep will deny bonding leave (extension) on the absence case",
    { retries: 0 },
    () => {
      cy.dependsOnPreviousPass([extension]);
      fineos.before();
      cy.unstash<Submission>("submission").then((submission) => {
        if (config("HAS_APRIL_UPGRADE") === "true") {
          fineosPages.ClaimPage.visit(submission.fineos_absence_id).deny(
            "Covered family relationship not established",
            true,
            true
          );
        } else {
          fineosPages.ClaimPage.visit(submission.fineos_absence_id).deny(
            "Claimant wages failed 30x rule",
            false,
            false
          );
        }
      });
    }
  );

  it("Will display the appropriate statuses for both leaves", () => {
    cy.dependsOnPreviousPass([denyExtension]);
    portal.before();
    portal.loginClaimant();
    cy.unstash<Submission>("submission").then((submission) => {
      portal.claimantGoToClaimStatus(submission.fineos_absence_id);
      portal.claimantAssertClaimStatus([
        { leave: "Serious Health Condition - Employee", status: "Approved" },
        { leave: "Child Bonding", status: "Denied" },
      ]);
    });
  });
});
