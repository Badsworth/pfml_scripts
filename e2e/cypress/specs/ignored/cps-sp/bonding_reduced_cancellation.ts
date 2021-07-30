import { fineos, portal, fineosPages } from "../../../actions";
import { getFineosBaseUrl } from "../../../config";
import { config } from "../../../actions/common";
import {
  findCertificationDoc,
  getDocumentReviewTaskName,
} from "../../../../src/util/documents";
import { onTab, waitForAjaxComplete } from "../../../actions/fineos";

describe("Approval (notifications/notices)", () => {
  after(() => {
    portal.deleteDownloadsFolder();
  });

  const credentials: Credentials = {
    username: config("PORTAL_USERNAME"),
    password: config("PORTAL_PASSWORD"),
  };

  it("Given a fully approved claim", { baseUrl: getFineosBaseUrl() }, () => {
    fineos.before();
    cy.visit("/");
    // Submit a claim via the API, including Employer Response.
    cy.task("generateClaim", "REDUCED_ER").then((claim) => {
      cy.stash("claim", claim.claim);
      cy.task("submitClaimToAPI", {
        ...claim,
        credentials,
      }).then((response) => {
        if (!response.fineos_absence_id) {
          throw new Error("Response contained no fineos_absence_id property");
        }

        cy.stash("submission", {
          application_id: response.application_id,
          fineos_absence_id: response.fineos_absence_id,
          timestamp_from: Date.now(),
        });

        const claimPage = fineosPages.ClaimPage.visit(
          response.fineos_absence_id
        );
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
        claimPage.approve();
        claimPage.triggerNotice("Designation Notice");
        cy.findByText("Record Cancellation", { selector: "span" }).click({
          force: true,
        });
        waitForAjaxComplete();
        cy.contains("td", "Known").click();
        cy.get(
          'input[title="Record Cancelled Time for the selected absence period"]'
        ).click();
        waitForAjaxComplete();
        cy.get('input[type="submit"][value="OK"]').click();
        waitForAjaxComplete();
        fineos.clickNext();
        waitForAjaxComplete();
        cy.get('select[id$="reportedBy"]').select("Employee");
        waitForAjaxComplete();
        cy.get('select[id$="receivedVia"]').select("Phone");
        waitForAjaxComplete();
        cy.get('select[id$="cancellationReason"]').select(
          "Employee Requested Cancellation"
        );
        waitForAjaxComplete();
        cy.get(
          'input[type="checkbox"][id$="MasterMultiSelectCB_CHECKBOX"]'
        ).click();
        cy.get('input[type="submit"][title="Apply"]').click();
        waitForAjaxComplete();
        fineos.clickNext();
        waitForAjaxComplete();
        cy.get('select[id$="period-decision-status"]').select("Approved");
        waitForAjaxComplete();
        cy.get(
          'input[type="checkbox"][id$="MasterMultiSelectCB_CHECKBOX"]'
        ).click();
        waitForAjaxComplete();
        cy.get('input[type="submit"][title="Apply"]').click();
        waitForAjaxComplete();
        fineos.clickNext();
        waitForAjaxComplete();
        onTab("Tasks");
        cy.get(
          'td[id="CaseTasksTabWidget_un67_FINEOS.WorkManager.Activities.ViewTasks.AbsenceCase_TasksView_cell"]'
        )
          .find("div")
          .click({ force: true });
        cy.findByText("All tasks").click();
        claimPage.tasks((tasks) => {
          tasks.assertTaskExists("Review and Decision Cancel Time Submitted");
        });
        claimPage.triggerNotice("Leave Cancellation Request");
        claimPage.documents((docsPage) => {
          docsPage.assertDocumentExists("Approved Time Cancelled");
        });
      });
    });
  });
});
