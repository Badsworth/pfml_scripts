import { fineos, fineosPages } from "../../actions";
import { getFineosBaseUrl } from "../../config";
import { Submission } from "../../../src/types";
import { config } from "../../actions/common";
import { extractLeavePeriod } from "../../../src/util/claims";
import { addDays, format } from "date-fns";

describe("Post-approval (notifications/notices)", () => {
  const credentials: Credentials = {
    username: config("PORTAL_USERNAME"),
    password: config("PORTAL_PASSWORD"),
  };
  it(
    "Submit a Care for a Family member claim for approval",
    { baseUrl: getFineosBaseUrl() },
    () => {
      fineos.before();
      cy.visit("/");
      //Submit a claim via the API, including Employer Response.
      cy.task("generateClaim", "CHAP_ER").then((claim) => {
        cy.stash("claim", claim);
        cy.task("submitClaimToAPI", {
          ...claim,
          credentials,
        }).then((response) => {
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
    }
  );

  it(
    'Generates a "Denial" document for extend time which will be "Change Request Denial"',
    { baseUrl: getFineosBaseUrl() },
    () => {
      fineos.before();
      cy.visit("/");

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
    }
  );
});
