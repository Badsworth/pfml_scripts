import { fineos, portal, fineosPages } from "../../actions";
import { getFineosBaseUrl, getLeaveAdminCredentials } from "../../config";
import { Submission } from "../../../src/types";
import { config } from "../../actions/common";
import { extractLeavePeriod } from "../../../src/util/claims";
import { assertValidClaim } from "../../../src/util/typeUtils";
import { format, addDays, parse } from "date-fns";

describe("Claim date change", () => {
  after(() => {
    portal.deleteDownloadsFolder();
  });

  const credentials: Credentials = {
    username: config("PORTAL_USERNAME"),
    password: config("PORTAL_PASSWORD"),
  };

  const submit = it(
    "Given a fully approved claim",
    { baseUrl: getFineosBaseUrl() },
    () => {
      fineos.before();
      cy.visit("/");
      // Submit a claim via the API, including Employer Response.
      cy.task("generateClaim", "BHAP1ER").then((claim) => {
        cy.stash("claim", claim);
        cy.task("submitClaimToAPI", {
          ...claim,
          credentials,
        }).then((response) => {
          if (!response.fineos_absence_id) {
            throw new Error("Response contained no fineos_absence_id property");
          }
          const [startDate, endDate] = extractLeavePeriod(claim.claim);
          cy.stash("submission", {
            application_id: response.application_id,
            fineos_absence_id: response.fineos_absence_id,
            timestamp_from: Date.now(),
          });
          const newStartDate = format(
            addDays(new Date(startDate), 1),
            "MM/dd/yyyy"
          );
          const newEndDate = format(
            addDays(new Date(endDate), 8),
            "MM/dd/yyyy"
          );
          cy.stash("changedLeaveDates", [newStartDate, newEndDate]);
          const claimPage = fineosPages.ClaimPage.visit(
            response.fineos_absence_id
          );
          claimPage.adjudicate((adjudication) => {
            adjudication.evidence((evidence) => {
              for (const document of claim.documents) {
                evidence.receive(document.document_type);
              }
            });
            cy.wait("@ajaxRender");
            cy.wait(200);
            adjudication.certificationPeriods((certificationPeriods) =>
              certificationPeriods.prefill()
            );
            adjudication.acceptLeavePlan();
          });
          claimPage.tasks((task) => {
            task.close("Bonding Certification Review");
            task.close("ID Review");
          });
          claimPage.approve();
          claimPage.tasks((task) => {
            task.add("Approved Leave Start Date Change");
            task.editActivityDescription(
              "Approved Leave Start Date Change",
              `Date change request: Move to ${newStartDate} - ${newEndDate}`
            );
          });
          claimPage.reviewClaim();
          cy.visit("/");
          const claimReviewed = fineosPages.ClaimPage.visit(
            response.fineos_absence_id
          );
          claimReviewed.adjudicate((adjudication) => {
            adjudication.editPlanDecision("Undecided");
            adjudication.certificationPeriods((certificationPeriods) =>
              certificationPeriods.remove()
            );
            adjudication.requestInformation((requestInformation) =>
              requestInformation.editRequestDates(newStartDate, newEndDate)
            );
            adjudication.certificationPeriods((certificationPeriods) =>
              certificationPeriods.prefill()
            );
          });
          claimReviewed.shouldHaveStatus("PlanDecision", "Undecided");
          claimReviewed.outstandingRequirements((outstandingRequirements) => {
            outstandingRequirements.add();
          });
          claimReviewed.tasks((task) => {
            task.close("Approved Leave Start Date Change");
            task.add("Update Paid Leave Case");
          });
        });
      });
    }
  );

  it("Should show the changed dates in Portal.", { retries: 0 }, () => {
    cy.dependsOnPreviousPass([submit]);
    portal.before();
    cy.visit("/");
    cy.unstash<DehydratedClaim>("claim").then(({ claim }) => {
      cy.unstash<Submission>("submission").then((submission) => {
        cy.unstash<string[]>("changedLeaveDates").then(
          ([startDate, endDate]) => {
            assertValidClaim(claim);
            portal.login(getLeaveAdminCredentials(claim.employer_fein));
            portal.selectClaimFromEmployerDashboard(
              submission.fineos_absence_id,
              "--"
            );
            const portalFormatStart = format(new Date(startDate), "M/d/yyyy");
            const portalFormatEnd = format(
              parse(endDate, "MM/dd/yyyy", new Date(endDate)),
              "M/d/yyyy"
            );
            portal.assertLeaveDatesAsLA(portalFormatStart, portalFormatEnd);
          }
        );
      });
    });
  });
});
