import { fineos, fineosPages } from "../../../actions";
import { FineosTasks, Submission } from "../../../../src/types";
import {
  clickBottomWidgetButton,
  waitForAjaxComplete,
} from "../../../actions/fineos";

//Portal and API call to submit claim
describe("Submit a claim through Portal: Verify it creates an absence case in Fineos", () => {
  const submission = it("Submit claim through API", () => {
    //@TODO adjust the generate claim for multiple different types and leave periods
    // Go to cypress.ts and adjust the CPS_SP by uncomment lines for what is needed to be tested.
    cy.task("generateClaim", "CPS_SP").then((claim) => {
      cy.stash("claim", claim);
      cy.task("submitClaimToAPI", claim).then((submission) => {
        cy.stash("submission", submission);
      });
    });
  });

  //Fineos check absence case here.
  it("Should check the claim in Fineos.", () => {
    cy.dependsOnPreviousPass([submission]);
    fineos.before();
    cy.unstash<DehydratedClaim>("claim").then((_claim) => {
      cy.unstash<Submission>("submission").then((submission) => {
        const claimPage = fineosPages.ClaimPage.visit(
          submission.fineos_absence_id
        );
        claimPage.tasks((tasksPage) => {
          // CPS-906-T CPS-906-U
          const hiddenTasks = [
            "Certification Overdue Notification",
            "Additional Information Review",
          ];
          hiddenTasks.forEach((task) => {
            cy.findByTitle(`Add a task to this case`).click({ force: true });
            cy.findByLabelText(`Find Work Types Named`).type(`${task}{enter}`);
            waitForAjaxComplete();
            cy.get("#NameChooseWorkTypeWidget").should(
              "not.contain.text",
              task
            );
            clickBottomWidgetButton("Cancel");
          });

          // [nameOfTask, SLA diff in days]
          const taskDiff: [FineosTasks, number][] = [
            ["Future or overlapping Absence Request exists", 3],
            ["Update Paid Leave Case", 1],
            ["Manual Intervention required to Approve Payments", 1],
            ["Escalate Employer Reported Other Income", 3],
            ["Absence Paid Leave Payments Failure", 1],
            ["Payment Change Request Received", 3],
            ["Manual Intervention required to Approve Periods", 1],
            // ["Conduct Hearing", 15], //Can't find task
            // ["Schedule Hearing", 15], //Can't find task
            // ["Review Appeal", 15], //Can't find task
            // ["Confirm Employment", 4], //Cant' find task
            // ["Employee Reported Other Leave", 5], //Got 2 days SLA diff.
          ];

          taskDiff.forEach(([task, diff]) => {
            cy.get("#TasksForCaseListViewWidget").then((el) => {
              // Skip adding the task if it's already there.
              if (el.text().includes(task)) return;
              tasksPage.add(task);
            });
            tasksPage.checkSLADifference(task, diff);
          });
        });
        claimPage.documents((_docs) => {
          // CPS-906-J (CPS-1105)
          cy.get('input[type="submit"][title="Add Document"]').click();
          const inboundDocuments = [
            "State managed Paid Leave Confirmation",
            "Appeal Form",
            "Appeals Supporting Documentation",
            "Covered Service Member Identification Proof",
            "Employer Paid Leave Policy",
            "Employer Proof of Payment",
            "Employer Response Additional Documentation",
            "Family Member Active Duty Service Proof",
            "Identification Proof",
            "Other Case Documentation",
            "Reimbursement Request Form",
            "Returned Payment",
          ];
          fineos.assertDocumentsInFolder(inboundDocuments, [
            "State of Mass",
            "Inbound Documents",
          ]);

          const outboundDocuments = [
            "Appeal Notice - Claim Decision Affirmed",
            "Appeal Notice - Claim Decision Changed",
            "Appeal Acknowledgment",
            "Approval Notice",
            "Denial Notice",
            "Hearing Scheduled Notice",
            "Reimbursement Approval",
            "Reimbursement Denial",
            "Request for more Information",
          ];
          fineos.assertDocumentsInFolder(outboundDocuments, [
            "State of Mass",
            "Outbound Documents",
          ]);

          const eForms = [
            "Employer Response to Leave Request",
            "Other Income - current version",
            "Other Leaves - current version",
          ];
          fineos.assertDocumentsInFolder(eForms, ["State of Mass", "eForms"]);
          // CPS-906-W (CPS-2405)
          const certificationDocuments = [
            "Own serious health condition form",
            "Pregnancy/Maternity form",
            "Child bonding evidence form",
            "Care for a family member form",
            "Military exigency form",
          ];
          fineos.assertDocumentsInFolder(certificationDocuments, [
            "State of Mass",
            "Inbound Documents",
          ]);
          clickBottomWidgetButton("Cancel");
        });
      });
    });
  });
});
