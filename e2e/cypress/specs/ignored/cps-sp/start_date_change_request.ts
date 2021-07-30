import { fineos, portal, fineosPages } from "../../../actions";
import { getFineosBaseUrl } from "../../../config";
import { extractLeavePeriod } from "../../../../src/util/claims";
import { format, addDays } from "date-fns";
import { config } from "../../../actions/common";

describe("Post-approval (notifications/notices)", () => {
  after(() => {
    portal.deleteDownloadsFolder();
  });

  const credentials: Credentials = {
    username: config("PORTAL_USERNAME"),
    password: config("PORTAL_PASSWORD"),
  };

  it(
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
          const newStartDate = format(
            addDays(new Date(startDate), 2),
            "MM/dd/yyyy"
          );
          const newEndDate = format(
            addDays(new Date(endDate), 2),
            "MM/dd/yyyy"
          );
          
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
          // Add new leave date
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
          // Click through to return to the absence hub
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
          const claimPage2 = fineosPages.ClaimPage.visit(
            res.fineos_absence_id
          );
          claimPage2.adjudicate((adjudication) => {
            adjudication.evidence((evidence) => {
              // Receive and approve all of the documentation for the claim.
              claim.documents.forEach((doc) =>
                evidence.receive(doc.document_type)
              );
            });
            adjudication.certificationPeriods((cert) => cert.prefill());
            adjudication.acceptLeavePlan();
            });
          // adjudicate process up until the plan decision is accepted
        });
      });
    }
  );

});
// cy.get('#DisplayCaseTabbedDialogWidget_un22_CaseTabControlBean_LeaveDetailsTab_cell > .TabOff').click();
// cy.get('.ListRow2 > :nth-child(11)').click();

// Under the “Selected Leave Plan” highlight the Leave Extension plan and choose to Reject the Leave Extension plan.

// Under the “Leave Request” highlight the Leave Extension claim.
// Click the Deny at the top right corner of the page.
