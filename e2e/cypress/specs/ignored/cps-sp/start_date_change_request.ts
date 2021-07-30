import { fineos, fineosPages } from "../../../actions";
import { getFineosBaseUrl } from "../../../config";
import { extractLeavePeriod } from "../../../../src/util/claims";
import { format, addDays } from "date-fns";
// import { onTab } from "../../../actions/fineos";
// import { clickTab } from "util/playwright";
import {
  findCertificationDoc,
  getDocumentReviewTaskName,
} from "../../../../src/util/documents";

describe("Post-approval (notifications/notices)", () => {
  const credentials: Credentials = {
    username: Cypress.env("E2E_PORTAL_USERNAME"),
    password: Cypress.env("E2E_PORTAL_PASSWORD"),
  };
  const extension = it(
    "Given a fully approved claim, a CSR agent can extend the claim's leave dates",
    { baseUrl: getFineosBaseUrl() },
    () => {
      fineos.before();
      cy.visit("/");
      // Submit a claim via the API, including Employer Response.
      cy.task("generateClaim", "CHAP_ER").then((claim) => {
        cy.stash("claim", claim);
        cy.task("submitClaimToAPI", {
          ...claim,
          credentials,
        }).then((res) => {
          const [startDate, endDate] = extractLeavePeriod(claim.claim);
          cy.stash("submission", {
            application_id: res.application_id,
            fineos_absence_id: res.fineos_absence_id,
            timestamp_from: Date.now(),
          });
          const newStartDate = format(
            addDays(new Date(startDate), 2),
            "MM/dd/yyyy"
          );
          const newEndDate = format(
            addDays(new Date(endDate), 2),
            "MM/dd/yyyy"
          );
          cy.stash("extensionLeaveDates", [startDate, newEndDate]);
          const claimPage = fineosPages.ClaimPage.visit(res.fineos_absence_id);
          claimPage.adjudicate((adjudication) => {
            adjudication.evidence((evidence) => {
              for (const document of claim.documents) {
                evidence.receive(document.document_type);
              }
            });
            fineos.waitForAjaxComplete();
            adjudication.certificationPeriods((certificationPeriods) =>
              certificationPeriods.prefill()
            );
            adjudication.acceptLeavePlan();
          });
          claimPage.tasks((task) => {
            task.close("Caring Certification Review");
            task.close("ID Review");
          });
          claimPage.approve();
          cy.findByText("Add Time").click({ force: true });
          cy.get('input[type="submit"][title="Add Time Off Period"]').click();
          fineos.waitForAjaxComplete();
          cy.get(".popup-container").within(() => {
            cy.labelled("Absence status").select("Known");
            fineos.waitForAjaxComplete();
            cy.get(
              "input[id='timeOffAbsencePeriodDetailsWidget_un19_startDate']"
            ).type(`{selectall}{backspace}${newStartDate}{enter}`);
            fineos.waitForAjaxComplete();
            cy.get(
              "input[id='timeOffAbsencePeriodDetailsWidget_un19_endDate']"
            ).type(`{selectall}{backspace}${newEndDate}{enter}`);
            fineos.waitForAjaxComplete();
            cy.get(
              "input[name='timeOffAbsencePeriodDetailsWidget_un19_startDateAllDay_CHECKBOX']"
            ).click();
            fineos.waitForAjaxComplete();
            cy.get(
              "input[name='timeOffAbsencePeriodDetailsWidget_un19_endDateAllDay_CHECKBOX']"
            ).click();
            fineos.waitForAjaxComplete();
            cy.get("input[title='OK']").click();
            fineos.waitForAjaxComplete();
            });
          cy.get('span[id="footerButtonsBar_cloned"]').contains("Next").click();
          fineos.waitForAjaxComplete();
          cy.get('span[id="footerButtonsBar_cloned"]').contains("Next").click();
          fineos.waitForAjaxComplete();
          cy.get('span[id="footerButtonsBar_cloned"]').contains("Next").click();
          fineos.waitForAjaxComplete();
          cy.get('span[id="footerButtonsBar_cloned"]').contains("Next").click();
          fineos.waitForAjaxComplete();
          cy.get('span[id="footerButtonsBar_cloned"]').contains("Next").click();
          fineos.waitForAjaxComplete();
          cy.get('span[id="footerButtonsBar_cloned"]').contains("OK").click();
          fineos.waitForAjaxComplete();
          // Complete adjudication process for new leave plan 
          claimPage.adjudicate((adjudication) => {
            adjudication.evidence((evidence) => {
              // Receive and approve all of the documentation for the claim.
              claim.documents.forEach((doc) =>
                evidence.receive(doc.document_type)
              );
            });
            adjudication.certificationPeriods((cert) => cert.prefill());
            adjudication.acceptLeavePlan();
          });
          claimPage.tasks((tasks) => {
            const certificationDoc = findCertificationDoc(claim.documents);
            const certificationTask = getDocumentReviewTaskName(
              certificationDoc.document_type
            );
            tasks.assertTaskExists("ID Review");
            tasks.assertTaskExists(certificationTask);
          });
          claimPage.shouldHaveStatus("Applicability", "Applicable");
          claimPage.shouldHaveStatus("Eligibility", "Met");
          claimPage.shouldHaveStatus("Evidence", "Satisfied");
          claimPage.shouldHaveStatus("Availability", "Time Available");
          claimPage.shouldHaveStatus("Restriction", "Passed");
          claimPage.shouldHaveStatus("PlanDecision", "Accepted");
          // claimPage.approve();
          // claimPage
          //   .triggerNotice("Leave Request Declined")
          //   .documents((docPage) =>
          //     docPage.assertDocumentExists("Denial Notice")
          //   );
          // cy.get('#DisplayCaseTabbedDialogWidget_un22_CaseTabControlBean_LeaveDetailsTab_cell > .TabOff').click();
          // cy.get('.ListRow2 > :nth-child(11)').click();

          // Under the “Selected Leave Plan” highlight the Leave Extension plan and choose to Reject the Leave Extension plan.
          
            // Under the “Leave Request” highlight the Leave Extension claim.
          // Click the Deny at the top right corner of the page.

        });
      });
    }
  );
});
