import { fineos, fineosPages } from "../../../actions";
import { getFineosBaseUrl } from "../../../config";
import { extractLeavePeriod } from "../../../../src/util/claims";
import { format, addDays } from "date-fns";
import { onTab } from "../../../actions/fineos";

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
            addDays(new Date(endDate), 1),
            "MM/dd/yyyy"
          );
          const newEndDate = format(
            addDays(new Date(endDate), 8),
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
            cy.wait("@ajaxRender");
            cy.wait(150);
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
          cy.wait("@ajaxRender");
          cy.wait(200);
          cy.get(".popup-container").within(() => {
            cy.labelled("Absence status").select("Known");
            cy.wait("@ajaxRender");
            cy.wait(200);
            cy.get(
              "input[id='timeOffAbsencePeriodDetailsWidget_un19_startDate']"
            ).type(`{selectall}{backspace}${newStartDate}{enter}`);
            cy.wait("@ajaxRender");
            cy.wait(200);
            cy.get(
              "input[id='timeOffAbsencePeriodDetailsWidget_un19_endDate']"
            ).type(`{selectall}{backspace}${newEndDate}{enter}`);
            cy.wait("@ajaxRender");
            cy.wait(200);
            cy.get(
              "input[name='timeOffAbsencePeriodDetailsWidget_un19_startDateAllDay_CHECKBOX']"
            ).click();
            cy.wait("@ajaxRender");
            cy.wait(200);
            cy.get(
              "input[name='timeOffAbsencePeriodDetailsWidget_un19_endDateAllDay_CHECKBOX']"
            ).click();
            cy.wait("@ajaxRender");
            cy.wait(200);
            cy.get("input[title='OK']").click();
            fineos.waitForAjaxComplete();
            cy.wait(200);
            cy.get('input[id="p9_un114_next"][value="Next"]').click();
            cy.wait(500);
            onTab("Additional Information");
          });
        });
      });
    }
  );
});
