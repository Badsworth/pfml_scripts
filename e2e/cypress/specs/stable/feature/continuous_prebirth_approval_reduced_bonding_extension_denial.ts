import { fineos, fineosPages, portal } from "../../../actions";
import { getFineosBaseUrl } from "../../../config";
import { Submission } from "../../../../src/types";
import { addMonths, addDays, format } from "date-fns";
import { config } from "../../../actions/common";

describe("Submit medical pre-birth application via the web portal", () => {
  const submission =
    it("Submits a Medical/Pregnancy claim through the API", () => {
      cy.task("generateClaim", "MED_PRE").then((claim) => {
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
  it(
    "CSR rep will approve reduced medical application",
    { retries: 0, baseUrl: getFineosBaseUrl() },
    () => {
      cy.dependsOnPreviousPass([submission]);
      fineos.before();
      cy.visit("/");
      cy.unstash<DehydratedClaim>("claim").then((claim) => {
        cy.unstash<Submission>("submission").then((submission) => {
          fineosPages.ClaimPage.visit(submission.fineos_absence_id)
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
  it(
    "CSR rep will add and deny bonding leave to the absence case",
    { retries: 0, baseUrl: getFineosBaseUrl() },
    () => {
      cy.dependsOnPreviousPass([submission]);
      fineos.before();
      // wait 30s before modifying approved absence case, there's a good chance we'll see a fatal fineos error page without waiting here
      cy.wait(1000 * 30);
      cy.unstash<Submission>("submission").then((submission) => {
        fineosPages.ClaimPage.visit(submission.fineos_absence_id)
          .benefitsExtension((benefitsExtension) => {
            const startDate = addMonths(new Date(), 2);
            const startDateFormatted = format(startDate, "MM/dd/yyyy");
            const endDateFormatted = format(
              addDays(startDate, 2),
              "MM/dd/yyyy"
            );
            benefitsExtension.extendLeave(
              startDateFormatted,
              endDateFormatted,
              true,
              "reduced"
            );
          })
          .adjudicate((adjudicate) => adjudicate.rejectLeavePlan())
          .deny("Evidence documents fail requirements", false);
      });
    }
  );
  it("Will display the appropriate statuses for both leaves", () => {
    cy.dependsOnPreviousPass([submission]);
    portal.before({
      claimantShowStatusPage: config("HAS_CLAIMANT_STATUS_PAGE") === "true",
    });
    const credentials: Credentials = {
      username: config("PORTAL_USERNAME"),
      password: config("PORTAL_PASSWORD"),
    };
    portal.login(credentials);
    cy.unstash<Submission>("submission").then((submission) => {
      // @todo: remove if statement after release into all envs
      if (config("HAS_CLAIMANT_STATUS_PAGE") === "true") {
        portal.claimantGoToClaimStatus(submission.fineos_absence_id);
        portal.claimantAssertClaimStatus([
          { leave: "Serious Health Condition - Employee", status: "Approved" },
          { leave: "Child Bonding", status: "Denied" },
        ]);
      }
    });
  });
});
