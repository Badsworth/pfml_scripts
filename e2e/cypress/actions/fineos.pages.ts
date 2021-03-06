import {
  Address,
  OtherIncome,
  PaymentPreferenceRequestBody,
  ReducedScheduleLeavePeriods,
  ApplicationRequestBody,
  AbsencePeriodResponse,
  Phone,
} from "../../src/_api";
import {
  FineosCloseTaskStep,
  FineosTasks,
  NonEmptyArray,
  PersonalIdentificationDetails,
  RequireNotNull,
  ValidClaim,
  ValidConcurrentLeave,
  ValidEmployerBenefit,
  ValidOtherIncome,
  ValidPreviousLeave,
} from "../../src/types";
import {
  isNotNull,
  isValidConcurrentLeave,
  isValidPreviousLeave,
  assertIsTypedArray,
  isValidEmployerBenefit,
  isValidOtherIncome,
  assertValidClaim,
} from "../../src/util/typeUtils";
import {
  dateToMMddyyyy,
  extractLeavePeriodType,
  getLeavePeriod,
  minutesToHoursAndMinutes,
} from "../../src/util/claims";
import {
  assertHasDocument,
  clickBottomWidgetButton,
  onTab,
  visitClaim,
  wait,
  waitForAjaxComplete,
  clickNext,
  getFixtureDocumentName,
  assertClaimStatus,
} from "./fineos";
import {
  addDays,
  differenceInBusinessDays,
  format,
  parseISO,
  startOfWeek,
  subDays,
  isBefore,
  isAfter,
  getHours,
  addBusinessDays,
} from "date-fns";
import { DocumentUploadRequest } from "../../src/api";
import { fineos } from ".";
import { LeaveReason } from "../../src/generation/Claim";
import { FineosCorrespondanceType, FineosDocumentType } from "./fineos.enums";
import { convertToTimeZone } from "date-fns-timezone";

type StatusCategory =
  | "Applicability"
  | "Eligibility"
  | "Evidence"
  | "Availability"
  | "Restriction"
  | "Protocols"
  | "PlanDecision";

type PlanDecisions = "Accepted" | "Pending Evidence" | "Rejected" | "Undecided";

/**
 * This is a page object for interacting with Fineos.
 *
 * It abstracts the concrete details of how an action is performed, and presents a descriptive API that allows the
 * test to describe _what_ needs to be done.
 *
 * There are two main constructs used in this API:
 *   * Enclosed callbacks (eg: adjudicate()), where an action is being performed within a given scope, and that scope
 *       only exists for a short period of time and should be "closed" immediately after.
 *   * Assertions/actions, (eg: assertStatus() or approve()), which are performed on the current page.
 *
 * To keep things DRY, both enclosed callbacks and assertions/actions should return the page object itself, allowing
 * calls to be chained together.
 */
export class ClaimPage {
  static visit(id: string): ClaimPage {
    visitClaim(id);
    return new ClaimPage();
  }

  addHistoricalAbsenceCase(upgrade?: boolean): HistoricalAbsence {
    return HistoricalAbsence.create(upgrade);
  }

  recordActualLeave<T>(cb: (page: RecordActualTime) => T): T {
    // Start the submission process.
    cy.findByText("Record Actual").click({ force: true });
    waitForAjaxComplete();
    return cb(new RecordActualTime());
  }

  paidLeave(cb: (page: PaidLeavePage) => unknown): this {
    cy.findByText("Absence Paid Leave Case", { selector: "a" }).click({
      force: true,
    });
    cb(new PaidLeavePage());
    cy.findByText("Absence Case", { selector: "a" }).click();
    return this;
  }
  // FINEOS April upgrade will adjust the in review process to which we don't have to click on the Adjudication
  // buton on the Absence Hub tab.
  adjudicateUpgrade(cb: (page: AdjudicationPage) => unknown): this {
    cb(new AdjudicationPage());
    cy.get("#footerButtonsBar input[value='OK']").click();
    return this;
  }

  adjudicate(cb: (page: AdjudicationPage) => unknown): this {
    cy.get('input[type="submit"][value="Adjudicate"]').click();
    cb(new AdjudicationPage());
    cy.get("#footerButtonsBar input[value='OK']").click();
    return this;
  }

  tasks(cb: (page: TasksPage) => unknown): this {
    onTab("Tasks");
    cb(new TasksPage());
    onTab("Absence Hub");
    return this;
  }

  appealDocuments(cb: (page: DocumentsPage) => unknown): this {
    onTab("Documents");
    cb(new DocumentsPage());
    return this;
  }

  appealTasks(cb: (page: TasksPage) => unknown): this {
    onTab("Tasks");
    cb(new TasksPage());
    return this;
  }

  documents(cb: (page: DocumentsPage) => unknown): this {
    onTab("Documents");
    cb(new DocumentsPage());
    onTab("Absence Hub");
    return this;
  }

  alerts(cb: (page: AlertsPage) => unknown): this {
    onTab("Alerts");
    cb(new AlertsPage());
    onTab("Absence Hub");
    return this;
  }

  availability(cb: (page: AvailabilityPage) => unknown): this {
    onTab("Availability");
    cb(new AvailabilityPage());
    onTab("Absence Hub");
    return this;
  }

  outstandingRequirements(
    cb: (page: OutstandingRequirementsPage) => unknown
  ): this {
    onTab("Outstanding Requirements");
    cb(new OutstandingRequirementsPage());
    onTab("Absence Hub");
    return this;
  }

  notes(cb: (page: NotesPage) => unknown): this {
    onTab("Notes");
    cb(new NotesPage());
    onTab("Absence Hub");
    return this;
  }

  leaveDetails(cb: (page: LeaveDetailsPage) => unknown): this {
    onTab("Leave Details");
    cb(new LeaveDetailsPage());
    return this;
  }

  benefitsExtension(cb: (page: BenefitsExtensionPage) => unknown): this {
    cy.findByText("Add Time").click({ force: true });
    cb(new BenefitsExtensionPage());
    return this;
  }

  shouldHaveStatus(category: StatusCategory, expected: string): this {
    const selector =
      category === "PlanDecision"
        ? `.divListviewGrid .ListTable td[id*='ListviewWidget${category}0']`
        : `.divListviewGrid .ListTable td[id*='ListviewWidget${category}Status0']`;
    cy.get(selector).should((element) => {
      expect(
        element,
        `Expected claim's "${category}" to be "${expected}"`
      ).to.have.text(expected);
    });
    return this;
  }

  triggerNotice(
    type:
      | "Designation Notice"
      | "SOM Generate Legal Notice"
      | "Leave Request Declined"
      | "Leave Request Withdrawn"
      | "Review Approval Notice"
      | "Leave Cancellation Request"
      | "Preliminary Designation"
      | "SOM Generate Appeals Notice"
      | "SOM Generate Employer Reimbursement Notice"
      | "Send Decision Notice"
      | "Review Denial Notice"
      | "Leave Allotment Change Notice"
  ): this {
    onTab("Task");
    onTab("Processes");
    cy.contains(".TreeNodeElement", type).click({
      force: true,
    });
    waitForAjaxComplete();
    // When we're firing time triggers, there's always the possibility that the trigger has already happened
    // by the time we get here. When this happens, the "Properties" button will be grayed out and unclickable.
    cy.get('input[type="submit"][value="Properties"]').then((el) => {
      if (el.is(":disabled")) {
        cy.log("Skipping trigger because this time trigger has already fired");
        return;
      }
      cy.wrap(el).click();
      waitForAjaxComplete();
      cy.get('input[type="submit"][value="Continue"]').click({ force: true });
      cy.contains(".TreeNodeContainer", type, {
        timeout: 20000,
      })
        .find("input[type='checkbox']")
        .should("be.checked");
    });

    return this;
  }

  approve(
    status: "Approved" | "Completed" = "Approved",
    upgrade: boolean | null | undefined = false
  ): this {
    // This button turns out to be unclickable without force, because selecting
    // it seems to scroll it out of view. Force works around that.
    if (upgrade) {
      cy.get('a[title="Approve the pending/in review leave request"]').click({
        force: true,
      });
    } else {
      cy.get('a[title="Approve the Pending Leaving Request"]').click({
        force: true,
      });
    }
    waitForAjaxComplete();
    assertClaimStatus(status);
    return this;
  }

  deny(reason: string, assertStatus = true, upgrade: boolean): this {
    cy.get("input[type='submit'][value='Adjudicate']").click();
    // Make sure the page is fully loaded by waiting for the leave plan to show up.
    cy.get("table[id*='selectedLeavePlans'] tr")
      .should("have.length", 1)
      .click();
    cy.get("input[type='submit'][value='Reject']").click();
    clickBottomWidgetButton("OK");
    const selector = upgrade
      ? 'a[title="Deny the pending/in review leave request"]'
      : 'a[title="Deny the Pending Leave Request"]';
    cy.get(selector).click();
    cy.get('span[id="leaveRequestDenialDetailsWidget"]')
      .find("select")
      .select(reason);
    cy.get('input[type="submit"][value="OK"]').click();
    // denying an extension for another reason will cause this assertion to fail
    assertStatus &&
      assertClaimStatus(upgrade ? "Previously denied" : "Declined", upgrade);
    return this;
  }

  addActivity(activity: string): this {
    cy.get("[id^=MENUBAR\\.CaseSubjectMenu]")
      .findByText("Add Activity")
      .click({ force: true })
      .parents("li")
      .findByText(activity)
      .click({ force: true });
    return this;
  }

  addCorrespondenceDocument(action: FineosCorrespondanceType): this {
    const document = new DocumentsPage();
    cy.get("[id^=MENUBAR\\.CaseSubjectMenu]")
      .findByText("Correspondence")
      .click({ force: true })
      .parents("li")
      .findByText(action)
      .click({ force: true });
    document.uploadDocumentAlt(action);
    return this;
  }

  // This will deny extended time in the Leave Details.
  // No assert ClaimStatus for Declined for the absence case
  // won't say "Declined".
  denyExtendedTime(reason: string, upgrade: boolean): this {
    const selector = upgrade
      ? 'a[title="Deny the pending/in review leave request"]'
      : 'a[title="Deny the Pending Leave Request"]';
    waitForAjaxComplete();
    cy.get("table[id$='leaveRequestListviewWidget']").within(() => {
      cy.get("tr.ListRowSelected").click();
    });
    cy.get(selector).click({
      force: true,
    });
    cy.get('span[id="leaveRequestDenialDetailsWidget"]')
      .find("select")
      .select(reason);
    cy.get('input[type="submit"][value="OK"]').click();
    return this;
  }

  approveExtendedTime(): this {
    waitForAjaxComplete();
    cy.get("table[id$='leaveRequestListviewWidget']").within(() => {
      cy.get("tr.ListRowSelected").click();
    });
    cy.get('a[title="Approve the Pending Leaving Request"]').click({
      force: true,
    });
    return this;
  }

  addAppeal(stashAppealCase: boolean): this {
    // This button turns out to be unclickable without force, because selecting
    // it seems to scroll it out of view. Force works around that.
    cy.get('a[title="Add Sub Case"]').click({
      force: true,
    });
    waitForAjaxComplete();
    cy.get('a[title="Create Appeal"]').click({
      force: true,
    });
    waitForAjaxComplete();
    if (stashAppealCase) {
      fineos.findAppealNumber("Appeal").then((appeal_case_id) => {
        cy.stash("appeal_case_id", appeal_case_id);
      });
    }
    return this;
  }

  addLeaveAllotmentChangeNotice(): this {
    cy.get('a[title="Correspondence"]').click({
      force: true,
    });
    waitForAjaxComplete();
    cy.findByLabelText("Leave Allotment Change Notice").click({
      force: true,
    });
    cy.get("#footerButtonsBar input[value='Next']").click();
    return this;
  }

  addEmployer(employer_fein: string): this {
    //Select employer from drop down menu
    cy.get("[id^=MENUBAR\\.CaseSubjectMenu]")
      .findByText("Add Participant")
      .click({ force: true })
      .parents("li")
      .findByText("Employer")
      .click({ force: true });

    //change radio to Organization
    cy.contains("label", "Organization").click();
    // input employer FEIN
    cy.get('input[type="text"][id$=_Social_Security_No\\._\\(SSN\\)]').type(
      employer_fein?.replace("-", "")
    );
    //Search
    cy.get('input[type="submit"][value="Search"]').click();
    waitForAjaxComplete();
    cy.get('input[type="submit"][value="OK"][id$=_searchPageOk]').click();
    return this;
  }

  withdraw(): this {
    cy.get('a[title="Withdraw the Pending Leave Request"').click({
      force: true,
    });
    cy.get("#leaveRequestWithdrawPopupWidget_PopupWidgetWrapper").within(() => {
      cy.findByLabelText("Withdrawal Reason").select("Employee Withdrawal");
      cy.findByText("OK").click({ force: true });
    });
    assertClaimStatus("Closed");
    return this;
  }

  reviewClaim(upgrade: boolean): this {
    onTab("Leave Details");
    cy.contains("td", "Approved").click();
    if (upgrade) {
      // Note in the new workflow for putting a claim into Review we are going directly to the Adjudication
      // instead of click on the Absence Hub. Then clicking the Adjudication button on the Absence Hub tab.
      cy.contains("button", "Review").click({ force: true });
      cy.wait("@reactRender");
      cy.get(`.ant-modal`)
        .should("be.visible")
        .within(() => {
          cy.get('input[id="secondOption"][type="radio"]').click();
          cy.contains("button", "OK").click();
        });
      waitForAjaxComplete();
      cy.contains(
        'span[id$="_openReviewDocumentLabel"]',
        "The leave request is now in review"
      );
      waitForAjaxComplete();
      cy.wait(500);
    } else {
      cy.get('input[title="Review a Leave Request"').click();
      waitForAjaxComplete();
      onTab("Absence Hub");
    }
    return this;
  }

  recordCancellation(): this {
    const recordCancelledTime = () => {
      cy.contains("td", "Known").click();
      cy.get(
        'input[title="Record Cancelled Time for the selected absence period"]'
      ).click();
      waitForAjaxComplete();
      cy.get('input[type="submit"][value="OK"]').click();
      waitForAjaxComplete();
      clickNext();
      waitForAjaxComplete();
      fineos.clickNext();
      waitForAjaxComplete();
    };
    const additionalReportingInformation = () => {
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
    };
    const makeDecision = () => {
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
    };

    cy.findByText("Record Cancellation", {
      selector: "span",
    }).click({
      force: true,
    });
    // steps for cancelling time
    recordCancelledTime();
    additionalReportingInformation();
    makeDecision();
    return this;
  }

  /**
   * This is used for the secure action testing in CPS ignored folder with security groups.
   * @param hasAction
   */
  suppressCorrespondence(hasAction: boolean): this {
    cy.contains("Options").click();
    if (hasAction) {
      cy.contains("Notifications").click({ force: true });
      cy.get("input[type='submit'][value='Suppress Notifications']").click();
      cy.contains(
        "Automatic Notifications and Correspondence have been suppressed."
      );
      cy.get("#alertsHeader").within(() => {
        cy.contains("Open").click({ force: true });
        waitForAjaxComplete();
        cy.contains(
          "Automatic Notifications and Correspondence have been suppressed."
        );
      });
      clickBottomWidgetButton("Close");
    } else {
      cy.contains(
        "span[title='Control is protected by a Secured Action.']",
        "Notifications"
      ).should("have.attr", "disabled");
    }
    return this;
  }

  /**
   * To test secure action task only with our current E2E test suite.
   * Suppress and remove suppression in the same task. Two options on how to remove the suppression when
   * clicking the Notification to remove the suppression in the pop-up widget is very flaky in the headless browser.
   * So the second option is to cancel the suppress notification instead.
   */
  removeSuppressCorrespondence(): this {
    cy.contains("Options").click();
    cy.contains("Notifications").click({ force: true });
    cy.get("input[type='submit'][value='Suppress Notifications']").click();
    cy.contains(
      "Automatic Notifications and Correspondence have been suppressed."
    );
    cy.get("#alertsHeader").within(() => {
      cy.contains("Open").click({ force: true });
      waitForAjaxComplete();
      cy.contains(
        "Automatic Notifications and Correspondence have been suppressed."
      );
    });
    cy.contains("Close Task").click();
    cy.get("table.PopupBean").within(() => {
      cy.get("input[type='submit'][value='Yes']")
        .first()
        .click({ force: true });
    });
    clickBottomWidgetButton("OK");
    return this;
  }
}

class AdjudicationPage {
  private activeTab: string;

  constructor() {
    this.activeTab = "Manage Request";
  }

  private onTab(...path: string[]) {
    if (this.activeTab !== path.join(",")) {
      for (const part of path) {
        onTab(part);
      }
      this.activeTab = path.join(",");
    }
  }

  restrictions(cb: (page: RestrictionsPage) => unknown): this {
    this.onTab("Restrictions");
    cb(new RestrictionsPage());
    return this;
  }

  evidence(cb: (page: EvidencePage) => unknown): this {
    this.onTab("Evidence");
    cb(new EvidencePage());
    return this;
  }

  certificationPeriods(cb: (page: CertificationPeriodsPage) => unknown): this {
    this.onTab("Evidence", "Certification Periods");
    cb(new CertificationPeriodsPage());
    return this;
  }

  requestEmploymentInformation() {
    this.onTab("Request Information", "Employment Information");
  }

  requestInformation(cb: (page: RequestInformationPage) => unknown): this {
    this.onTab("Request Information", "Request Details");
    cb(new RequestInformationPage());
    return this;
  }

  acceptLeavePlan(): this {
    this.onTab("Manage Request");
    cy.get("input[type='submit'][value='Accept']").click({ force: true });
    return this;
  }

  rejectLeavePlan(): this {
    this.onTab("Manage Request");
    cy.get("input[type='submit'][value='Reject']").click({ force: true });
    return this;
  }

  editPlanDecision(planDecision: PlanDecisions) {
    this.onTab("Manage Request");
    waitForAjaxComplete();
    cy.get("input[type='submit'][value='Evaluate Plan']").click();
    cy.findByLabelText("Leave Plan Status").select(planDecision);
    cy.get("#footerButtonsBar input[value='OK']").click();
  }

  availability(cb: (page: AvailabilityPage) => unknown): this {
    this.onTab("Availability");
    cb(new AvailabilityPage());
    this.onTab("Manage Request");
    return this;
  }

  paidBenefits(cb: (page: PaidBenefitsPage) => unknown): this {
    this.onTab("Paid Benefits");
    cb(new PaidBenefitsPage());
    this.onTab("Manage Request");
    return this;
  }

  exitWithoutSaving(): this {
    clickBottomWidgetButton("Cancel");
    return this;
  }

  clickOK(): void {
    cy.get("#footerButtonsBar input[value='OK']").click();
  }

  doNothing(): this {
    return this;
  }
}

type EvidenceStatus = {
  evidenceType: string;
  receipt?: "Pending" | "Received" | "Not Received";
  decision?: "Pending" | "Satisfied" | "Not Satisfied" | "Waived";
  reason?: string;
};

class EvidencePage {
  receive(
    evidenceType: string,
    receipt = "Received" as const,
    decision = "Satisfied" as const,
    reason = "Evidence has been reviewed and approved"
  ): this {
    cy.findByText(evidenceType).click();
    cy.contains("tr", evidenceType).should("have.class", "ListRowSelected");
    cy.findByText("Manage Evidence").click({
      force: true,
    });
    // Focus inside popup. Note: There should be no need for an explicit wait here because
    // Cypress will not move on until the popup has been rendered.
    cy.get(".WidgetPanel_PopupWidget").within(() => {
      cy.findByLabelText("Evidence Receipt").select(receipt);
      cy.findByLabelText("Evidence Decision").select(decision);
      cy.findByLabelText("Evidence Decision Reason").type(
        `{selectall}{backspace}${reason}`
      );
      cy.findByText("OK").click({ force: true });
      // Wait till modal has fully closed before moving on.
    });
    // Wait until the table has updated with the new status before we attempt to move on.
    this.assertEvidenceStatus({
      evidenceType,
      receipt,
      decision,
      reason,
    });
    cy.contains(".ListTable tr", evidenceType).should((row) => {
      expect(row.find("td:nth-child(3)")).to.contain.text(receipt);
      expect(row.find("td:nth-child(5)")).to.contain.text(decision);
    });
    return this;
  }

  /**
   * Checks that there's evidence with given status, which includes receipt, decision, reason.
   * @example
   * evidence.assertEvidenceStatus({
   *  evidenceType: "Military exigency form",
   *  decision: "Pending",
   *  receipt: "Pending",
   * });
   */
  assertEvidenceStatus({
    evidenceType,
    receipt,
    decision,
    reason,
  }: EvidenceStatus) {
    cy.contains("tr", evidenceType).should("be.visible");
    if (receipt)
      cy.contains("tr", evidenceType).should("contain.text", receipt);
    if (decision)
      cy.contains("tr", evidenceType).should("contain.text", decision);
    if (reason) cy.contains("tr", evidenceType).should("contain.text", reason);
  }

  requestAdditionalInformation(
    documentType: string,
    incomplete: Record<string, string>,
    comment: string
  ): this {
    cy.contains(".ListTable td", documentType).click();
    cy.get("input[type='submit'][value='Additional Information']").click();
    for (const [part, message] of Object.entries(incomplete)) {
      cy.contains("#AddExtraDataWidget tr", part).within(() => {
        cy.root().find("input[type='checkbox']").click();
        cy.root().find("input[type='text']").type(message);
      });
    }
    cy.get("textarea[name*='missingInformationBox']").type(comment);
    clickBottomWidgetButton("OK");
    cy.wait("@ajaxRender");
    cy.wait(200);
    return this;
  }
}

class CertificationPeriodsPage {
  prefill() {
    waitForAjaxComplete();
    cy.get("input[value='Prefill with Requested Absence Periods']").click();
    cy.get("#PopupContainer input[value='Yes']").click();
    return this;
  }

  remove() {
    cy.get(
      "input[type='submit'][title='Remove all certification periods']"
    ).click();
    cy.get("#PopupContainer input[value='Yes']").click();
    waitForAjaxComplete();
    cy.get("#PopupContainer input[value='Yes']").click();
    waitForAjaxComplete();
    cy.get("#PopupContainer input[value='Yes']").click();
    return this;
  }
}

class RequestInformationPage {
  private enterNewLeaveDates(newStartDate: string, newEndDate: string) {
    cy.get("input[id*='startDate']").first().click();
    cy.get("input[id*='startDate']")
      .first()
      .type(`{selectall}{backspace}${newStartDate}{enter}`);
    waitForAjaxComplete();
    cy.get("input[id*='endDate']").first().click();
    cy.get("input[id*='endDate']")
      .first()
      .type(`{selectall}{backspace}${newEndDate}{enter}`);
    waitForAjaxComplete();
    cy.get("input[type='button'][title='OK']").click();
    waitForAjaxComplete();
  }

  editRequestDates(newStartDate: string, newEndDate: string): ClaimPage {
    waitForAjaxComplete();
    cy.get(
      "table[id^='timeOffAbsencePeriodsListview'][class='ListTable responsive-table']"
    ).within(() => {
      cy.get("tr").then(
        ($el) => expect($el.hasClass("ListRowSelected")).to.be.true
      );
    });
    cy.get("input[value='Edit']").click();
    cy.get("#PopupContainer input[value='Yes']").click();
    waitForAjaxComplete();
    this.enterNewLeaveDates(newStartDate, newEndDate);
    waitForAjaxComplete();
    // completing this process redirects us to the "Manage Request" tab
    return new ClaimPage();
  }

  assertHoursWorkedPerWeek(hours_worked_per_week: number) {
    onTab("Employment Information");
    cy.findByLabelText("Hours worked per week").should((input) => {
      expect(
        input,
        `Hours worked per week should be: ${hours_worked_per_week} hours`
      )
        .attr("value")
        .equal(String(hours_worked_per_week));
    });
    onTab("Request Details");
  }
}

class OutstandingRequirementsPage {
  add() {
    waitForAjaxComplete();
    cy.get("input[value='Add']").click();
    cy.get(
      "#AddManagedRequirementPopupWidget_PopupWidgetWrapper input[type='submit'][value='Ok']"
    ).click();
    cy.get("#footerButtonsBar input[value='OK']").click({ force: true });
    cy.wait(300);
  }

  complete(receipt: string, reason: string, hasAccess: boolean): this {
    if (hasAccess) {
      cy.wait("@ajaxRender");
      cy.wait(200);
      cy.get("input[value='Complete']").click();
      cy.get("#CompletionReasonWidget_PopupWidgetWrapper").within(() => {
        cy.findByLabelText("Completion Reason").select(receipt);
        cy.findByLabelText("Completion Notes").type(
          `{selectall}{backspace}${reason}`
        );
        cy.findByText("Ok").click({ force: true });
      });
    } else {
      cy.wait("@ajaxRender");
      cy.wait(200);
      cy.get("input[value='Complete']").click();
      cy.get(`span[id^="PageMessage1"]`).should(
        "contain.text",
        "You do not have the required secured action to mark all of the selected Outstanding Requirements as Complete."
      );
    }
    return this;
  }

  suppress(reason: string, notes: string, hasAccess: boolean): this {
    if (hasAccess) {
      cy.wait("@ajaxRender");
      cy.wait(200);
      cy.get("input[value='Suppress']").click();
      cy.get("#SuppressionReasonWidget_PopupWidgetWrapper").within(() => {
        cy.findByLabelText("Suppression Reason").select(reason);
        cy.findByLabelText("Suppression Notes").type(
          `{selectall}{backspace}${notes}`
        );
        cy.findByText("Ok").click({ force: true });
      });
      cy.wait(200);
    } else {
      cy.wait("@ajaxRender");
      cy.wait(200);
      cy.get("input[value='Suppress']").click();
      cy.get(`span[id^="PageMessage1"]`).should(
        "contain.text",
        "You do not have the required secured action to mark all of the selected Outstanding Requirements as Suppressed."
      );
    }
    return this;
  }

  removeOR(hasAccess: boolean): this {
    if (hasAccess) {
      cy.wait("@ajaxRender");
      cy.wait(200);
      cy.get("input[value='Remove']").click();
      cy.get("#PopupContainer input[type='submit'][value='Yes']").click();
    } else {
      cy.wait("@ajaxRender");
      cy.wait(200);
      cy.get("input[value='Remove']").click();
      cy.get(`span[id^="PageMessage1"]`).should(
        "contain.text",
        "You do not have the required secured action to remove all of the selected Outstanding Requirements"
      );
    }
    return this;
  }

  reopen(hasAccess: boolean): this {
    if (hasAccess) {
      cy.wait("@ajaxRender");
      cy.wait(200);
      cy.get("input[value='Reopen']").click();
    } else {
      cy.wait("@ajaxRender");
      cy.wait(200);
    }
    return this;
  }
}

class TasksPage {
  /**
   * Called from the tasks page, asserts that a particular task is found.
   * @param name
   */
  assertTaskExists(name: FineosTasks): this {
    cy.get("table[id*='TasksForCaseWidget']").should((table) => {
      expect(table, `Expected to find a "${name}" task`).to.have.descendants(
        `tr td:nth-child(6)[title="${name}"]`
      );
    });
    return this;
  }

  /**
   * Adds a task to a claim and asserts it has been assigned to DFML Program Integrity
   * @param name name of the task to be added
   */
  add(name: FineosTasks): this {
    cy.findByTitle(`Add a task to this case`).click({ force: true });
    // Search for the task type
    cy.findByLabelText(`Find Work Types Named`).type(`${name}{enter}`);
    // Create task
    cy.findByTitle(name).click({ force: true });
    clickBottomWidgetButton("Next");
    return this;
  }

  close(name: FineosTasks): this {
    cy.contains("td", name).click();
    waitForAjaxComplete();
    cy.get('input[title="Close selected task"]').click();
    waitForAjaxComplete();
    return this;
  }

  select(task: string): this {
    // Find  task
    cy.contains("tbody", "This case and its subcases").within(() => {
      cy.findByText(task).click();
    });
    cy.get(
      `[id^="activitytabs"][id$="FINEOS.WorkManager.Activities.ViewActivityDialogue.Task"]`
    ).should("contain.text", task);
    return this;
  }

  /**Checks difference between creation date and target date of a task */
  checkSLADifference(task: FineosTasks, diffInDays: number): this {
    this.select(task);
    cy.get(
      `[id^="activitytabs"][id$="FINEOS.WorkManager.Activities.ViewActivityDialogue.Task"]`
    ).then((el) => {
      const creationDate = el
        .find(`[id^="BasicDetailsUsersDeptWidget"][id$="_CreationDate"]`)
        .text()
        .split(" ")[0];
      const targetDate = el
        .find(`[id^="ActivityTargetDates"][id$="_TargetDate"]`)
        .text()
        .split(" ")[0];
      console.log(creationDate);
      console.log(targetDate);
      expect(
        differenceInBusinessDays(new Date(targetDate), new Date(creationDate))
      ).to.eq(diffInDays);
    });
    return this;
  }

  assertIsAssignedToUser(task: FineosTasks, user: string): this {
    this.select(task);
    // Assert it's assigned to given user
    cy.get(`span[id^="BasicDetailsUsersDeptWidget"][id$="AssignedTo"]`).should(
      "contain.text",
      `${user}`
    );
    return this;
  }

  assertIsAssignedToDepartment(task: FineosTasks, department: string): this {
    // Find  task
    this.select(task);
    // Assert it's in given department
    cy.get(`span[id^="BasicDetailsUsersDeptWidget"][id$="Department"]`).should(
      "contain.text",
      `${department}`
    );
    return this;
  }

  editActivityDescription(
    name: string,
    comment: string,
    upgrade: boolean | null | undefined = false
  ): this {
    cy.contains("td", "Approved Leave Start Date Change").click();
    cy.wait("@ajaxRender");
    cy.get('input[title="Edit this Activity"').click();
    cy.wait("@ajaxRender");
    if (upgrade) {
      cy.get("textarea[name*='BasicDetailsWidget1_']").type(comment);
    } else {
      cy.get("textarea[name*='BasicDetailsWidget1_un11_Description']").type(
        comment
      );
    }
    cy.wait(150);
    cy.get("#footerButtonsBar input[value='OK']").click();
    return this;
  }

  closeAppealReview(): this {
    cy.findByText("Appeal", { selector: "a" }).click();
    waitForAjaxComplete();
    cy.contains("td", "Review Appeal").click();
    waitForAjaxComplete();
    cy.get('input[title="Close selected task"]').click();
    waitForAjaxComplete();
    fineos.clickBottomWidgetButton("OK");
    waitForAjaxComplete();
    return this;
  }

  closeConductHearing(): this {
    cy.findByText("Appeal", { selector: "a" }).click();
    waitForAjaxComplete();
    cy.contains("td", "Conduct Hearing").click();
    waitForAjaxComplete();
    cy.contains("td", "Closed - Claim Decision Changed").click();
    waitForAjaxComplete();
    fineos.clickBottomWidgetButton("OK");
    waitForAjaxComplete();
    assertClaimStatus("Closed - Claim Decision Changed");
    return this;
  }

  closeWithAdditionalSelection(
    name: FineosTasks,
    selection: FineosCloseTaskStep
  ): this {
    cy.get(`table[id*="TasksForCaseWidget"]`).findByText(name).click();
    waitForAjaxComplete();
    cy.get('input[title="Close selected task"]').click({ force: true });
    waitForAjaxComplete();
    cy.contains("td", selection).click();
    waitForAjaxComplete();
    fineos.clickBottomWidgetButton("OK");
    waitForAjaxComplete();
    return this;
  }

  all(): this {
    cy.get("input[type='radio'][value$='_allTasks']").click();
    waitForAjaxComplete();
    return this;
  }

  returnSubTasksTab(): this {
    cy.get(
      'td[id$="_FINEOS.WorkManager.Activities.ViewTasks.AbsenceCase_TasksView_cell"]'
    ).click();
    return this;
  }
}

/**
 * This class represents the documents page/tab within the broader Claim page/view in Fineos.
 */
export class DocumentsPage {
  assertDocumentExists(documentName: string): this {
    assertHasDocument(documentName);
    return this;
  }

  changeDocType(
    oldDocType: DocumentUploadRequest["document_type"],
    newDocType:
      | DocumentUploadRequest["document_type"]
      | "State managed Paid Leave Confirmation",
    shouldBeAvailable = true
  ): void {
    // Select the document
    cy.get(
      'table[id^="DocumentsForCaseListviewWidget_"][id$="_DocumentsViewControl"]'
    )
      .contains("tr", oldDocType)
      .click()
      .should("have.class", "ListRowSelected");
    // Open document properties
    cy.findByTitle("Document Properties").click();
    // Do if this action should be available
    if (shouldBeAvailable) {
      // Find and select a new document type.
      cy.findByTitle("Document Search.").click({ force: true });
      onTab("Search");
      cy.findByLabelText("Business Type").type(newDocType);
      cy.get('input[type="submit"][value="Search"]').click();
      clickBottomWidgetButton("OK");
      // Assert that the document typ has been changed correctly
      cy.findByTitle("Document Search.")
        .parent()
        .prev()
        .should("contain.text", newDocType);
    } else {
      cy.contains("td", "Document Type")
        .next()
        .should("not.contain.html", 'title="Document Search."');
    }
    clickBottomWidgetButton(shouldBeAvailable ? "OK" : "Close");
    if (shouldBeAvailable)
      cy.get(
        'table[id^="DocumentsForCaseListviewWidget_"][id$="_DocumentsViewControl"]'
      ).should("contain.text", newDocType);
  }

  /**
   * Goes through the document upload process and returns back to the documents page
   * @param businessType - name of the document type in fineos
   * @returns
   */
  uploadDocument(documentType: FineosDocumentType): this {
    this.startDocumentCreation(documentType);
    cy.get("input[type='file']").attachFile(
      `./${getFixtureDocumentName(documentType)}.pdf`
    );
    clickBottomWidgetButton();
    this.assertDocumentExists(documentType);
    return this;
  }

  uploadDocumentAlt(documentType: FineosDocumentType): this {
    cy.get("input[type='file']").attachFile(
      `./${getFixtureDocumentName(documentType)}.pdf`
    );
    clickBottomWidgetButton();
    onTab("Documents");
    this.assertDocumentExists(documentType);
    onTab("Absence Hub");
    return this;
  }

  /**
   * Asserts the total amount of times a document has been uploaded to a case
   * @param type
   * @param occurences
   */
  assertDocumentUploads(
    type: DocumentUploadRequest["document_type"],
    occurences = 1
  ): this {
    cy.get(`a:contains("${type}")`).should("have.length", occurences);
    return this;
  }

  /**
   * Starts the document creation process and finds the right document type.
   */
  private startDocumentCreation(documentType: string): void {
    cy.get('input[type="submit"][title="Add Document"]').click();
    onTab("Search");
    cy.findByLabelText("Business Type").type(`${documentType}{enter}`);
    clickBottomWidgetButton();
  }

  submitLegacyEmployerBenefits(
    benefits: (ValidEmployerBenefit | ValidOtherIncome)[]
  ): this {
    this.startDocumentCreation(`Other Income`);
    benefits.forEach(this.fillLegacyEmployerBenefit);
    clickBottomWidgetButton();
    this.assertDocumentExists("Other Income");
    return this;
  }

  private fillLegacyEmployerBenefit(
    benefitOrIncome: ValidEmployerBenefit | ValidOtherIncome,
    index: number
  ) {
    // Will you receive wage replacement during your leave?
    cy.get(`select[id$=_ReceiveWageReplacement${index > 0 ? index + 1 : ""}]`)
      .should("be.visible")
      .select(`Yes`);
    // Through what type of program will you receive your wage replacement benefit?
    cy.get(`select[id$=_ProgramType${index > 0 ? index + 1 : ""}]`)
      .should("be.visible")
      .select(
        isValidOtherIncome(benefitOrIncome) ? `Non-Employer` : `Employer`
      );
    // Choose type of wage replacement
    // This one is either bugged or is working in a mysterious way. Skips even indexes
    cy.get(
      `select[id$=_WRT${
        index > 0
          ? index * 2 + (isValidOtherIncome(benefitOrIncome) ? 2 : 1)
          : index + 1
      }]`
    )
      .should("be.visible")
      .select(
        `${
          isValidOtherIncome(benefitOrIncome)
            ? benefitOrIncome.income_type
            : benefitOrIncome.benefit_type
        }`
      );
    // When will you start receiving this income?
    cy.get(
      `input[type=text][id$=_StartDate${index > 0 ? index + 1 : ""}]`
    ).type(
      `${dateToMMddyyyy(
        isValidOtherIncome(benefitOrIncome)
          ? benefitOrIncome.income_start_date
          : benefitOrIncome.benefit_start_date
      )}{enter}`
    );
    // When will you stop receiving this income?
    cy.get(`input[type=text][id$=_EndDate${index > 0 ? index + 1 : ""}]`).type(
      `${dateToMMddyyyy(
        isValidOtherIncome(benefitOrIncome)
          ? benefitOrIncome.income_end_date
          : benefitOrIncome.benefit_end_date
      )}{enter}`
    );

    cy.get(`input[type=text][id$=_Amount${index > 0 ? index + 1 : ""}]`).type(
      `{selectall}{backspace}${
        isValidOtherIncome(benefitOrIncome)
          ? benefitOrIncome.income_amount_dollars
          : benefitOrIncome.benefit_amount_dollars
      }`
    );

    cy.get(`select[id$=_Frequency${index > 0 ? index + 1 : ""}]`).select(
      `${
        isValidOtherIncome(benefitOrIncome)
          ? benefitOrIncome.income_amount_frequency
          : benefitOrIncome.benefit_amount_frequency
      }`
    );
  }

  setDocumentComplete(documentName: string): this {
    cy.get(`table[id*='DocumentsForCaseListviewWidget']`)
      .contains("a", documentName)
      .first()
      .parent()
      .click({ force: true });
    waitForAjaxComplete();
    cy.findByDisplayValue("Properties").click();
    waitForAjaxComplete();
    cy.get('span[id*="status_WRAPPER"]').find("select").select("Completed");
    waitForAjaxComplete();
    clickBottomWidgetButton("OK");
    return this;
  }

  addDocument(documentName: string): this {
    this.startDocumentCreation(documentName);
    waitForAjaxComplete();
    clickBottomWidgetButton("Next");
    waitForAjaxComplete();
    return this;
  }

  /**
   * Submits the "Other Income - current version" eForm. If succesfull returns back to the "Documents" page.
   * @param employer_benefits
   * @param other_incomes
   */
  submitOtherBenefits({
    employer_benefits,
    other_incomes,
  }: Pick<
    ApplicationRequestBody,
    "other_incomes" | "employer_benefits"
  >): this {
    this.startDocumentCreation("Other Income - current version");
    const alertSpy = cy.spy(window, "alert");

    if (employer_benefits) {
      assertIsTypedArray(employer_benefits, isValidEmployerBenefit);
      employer_benefits.forEach(this.fillEmployerBenefitData);
    }

    if (other_incomes)
      other_incomes.forEach(this.fillIncomeFromOtherSourcesData);

    cy.get(`#PageFooterWidget input[value="OK"]`).should((el) => {
      el.trigger("click");
      expect(alertSpy.callCount).to.eq(0);
      alertSpy.resetHistory();
    });
    this.assertDocumentExists("Other Income - current version");
    return this;
  }

  private fillIncomeFromOtherSourcesData(
    other_income: OtherIncome,
    i: number
  ): void {
    i += 1;
    // Here we have the same problem, multiple possible incomes, same labels, the only difference is the number at the end of the id
    // The initial question has id's starting from 7
    // Will you receive income from any other sources during your leave dates for paid leave?
    cy.get(`select[id$=ReceiveWageReplacement${i + 6}]`).select("Yes");

    const otherIncomeTypeMap: Record<
      NonNullable<typeof other_income.income_type>,
      string
    > = {
      "Disability benefits under Gov't retirement plan":
        "Disability benefits under a governmental retirement plan such as STRS or PERS",
      "Earnings from another employment/self-employment":
        "Earnings from another employer or through self-employment",
      "Jones Act benefits": "Jones Act benefits",
      "Railroad Retirement benefits": "Railroad Retirement benefits",
      "Unemployment Insurance": "Unemployment Insurance",
      "Workers Compensation": "Workers Compensation",
      SSDI: "Social Security Disability Insurance",
    };
    // What kind of income is it?
    if (isNotNull(other_income.income_type))
      cy.get(`select[id$=OtherIncomeNonEmployerBenefitWRT${i}]`).select(
        otherIncomeTypeMap[other_income.income_type]
      );

    // When will you start receiving this income?
    if (isNotNull(other_income.income_start_date))
      cy.get(
        `input[type=text][id$=OtherIncomeNonEmployerBenefitStartDate${i}]`
      ).type(`${dateToMMddyyyy(other_income.income_start_date)}{enter}`);

    // When will you stop receiving this income?
    if (isNotNull(other_income.income_end_date))
      cy.get(
        `input[type=text][id$=OtherIncomeNonEmployerBenefitEndDate${i}]`
      ).type(`${dateToMMddyyyy(other_income.income_end_date)}{enter}`);

    // How much will you receive? (Optional)
    if (isNotNull(other_income.income_amount_dollars))
      cy.get(
        `input[type=text][id$=OtherIncomeNonEmployerBenefitAmount${i}]`
      ).type(`{selectall}{backspace}${other_income.income_amount_dollars}`);
    // How often will you receive this amount? (Optional)
    const otherIncomeFrequencyMap: Record<
      NonNullable<typeof other_income.income_amount_frequency>,
      string
    > = {
      "In Total": "One Time / Lump Sum",
      "Per Day": "Per Day",
      "Per Month": "Per Month",
      "Per Week": "Per Week",
    };
    if (isNotNull(other_income.income_amount_frequency))
      cy.get(`select[id$=OtherIncomeNonEmployerBenefitFrequency${i}]`).select(
        otherIncomeFrequencyMap[other_income.income_amount_frequency]
      );
  }

  private fillEmployerBenefitData(
    benefit: ValidEmployerBenefit,
    i: number
  ): void {
    i += 1;
    // The convoluted type is so that we can update the map appropriately when the EmployerBenefit type changes
    const employerBenefitTypeMap: Record<
      ValidEmployerBenefit["benefit_type"],
      string
    > = {
      "Accrued paid leave": "Accrued paid leave",
      "Short-term disability insurance":
        "Temporary disability insurance (Long- or Short-term)",
      "Permanent disability insurance": "Permanent disability insurance",
      "Family or medical leave insurance":
        "Family or medical leave, such as a parental leave policy",
      Unknown: "Please select",
    };
    // Will you receive any employer-sponsored benefits from this employer during your leave?
    cy.get(`select[id$=ReceiveWageReplacement${i}]`).select("Yes");

    // What kind of employer benefit is it?
    cy.get(`select[id$=V2WRT${i}]`).select(
      employerBenefitTypeMap[benefit.benefit_type]
    );

    // Is this benefit full salary continuation?
    cy.get(`select[id$=SalaryContinuation${i}]`).select(
      benefit.is_full_salary_continuous === true ? "Yes" : "No"
    );
    // When will you start receiving this income?
    cy.get(`input[type=text][id$=V2StartDate${i}]`).type(
      `${dateToMMddyyyy(benefit.benefit_start_date)}{enter}`
    );
    /**
     * @note Following fields are marked as optional in Fineos, but are not optional in the claimant portal.
     */
    // When will you stop receiving this income? (Optional)
    if (isNotNull(benefit.benefit_end_date))
      cy.get(`input[type=text][id$=V2EndDate${i}]`).type(
        `${dateToMMddyyyy(benefit.benefit_end_date)}{enter}`
      );
    // How much will you receive? (Optional)
    if (isNotNull(benefit.benefit_amount_dollars))
      cy.get(`input[type=text][id$=V2Amount${i}]`).type(
        `{selectall}{backspace}${benefit.benefit_amount_dollars}`
      );
    const benefitFrequencyMap = {
      "In Total": "One Time / Lump Sum" as const,
      "Per Day": "Per Day" as const,
      "Per Month": "Per Month" as const,
      "Per Week": "Per Week" as const,
      Unknown: "Please select" as const,
    };
    // How often will you receive this amount? (Optional)
    if (isNotNull(benefit.benefit_amount_frequency))
      cy.get(`select[id$=V2Frequency${i}]`).select(
        benefitFrequencyMap[benefit.benefit_amount_frequency]
      );
  }

  /**
   * Submits other leaves within the "Other Leaves - current version" eForm. If succesfull returns back to the "Documents" page.
   * @todo - make it take other leaves as parameters.
   * @param previous_leaves_other_reason
   * @param accrued_leaves - All of the accrued paid leaves to be used during the dates of current PFML leave. Currently are listed within the
   * @returns
   */
  submitOtherLeaves({
    previous_leaves_other_reason,
    previous_leaves_same_reason,
    concurrent_leave,
  }: {
    previous_leaves_other_reason?: ApplicationRequestBody["previous_leaves_other_reason"];
    previous_leaves_same_reason?: ApplicationRequestBody["previous_leaves_same_reason"];
    concurrent_leave?: ApplicationRequestBody["concurrent_leave"];
  }): this {
    this.startDocumentCreation("Other Leaves - current version");
    // Reports all of the previous leaves with same reason
    if (previous_leaves_other_reason) {
      assertIsTypedArray(previous_leaves_other_reason, isValidPreviousLeave);
      previous_leaves_other_reason.forEach(this.fillPreviousLeaveData);
    }
    if (previous_leaves_same_reason) {
      assertIsTypedArray(previous_leaves_same_reason, isValidPreviousLeave);
      previous_leaves_same_reason.forEach(this.fillPreviousLeaveData);
    }
    if (isValidConcurrentLeave(concurrent_leave))
      this.fillAccruedLeaveData(concurrent_leave);
    clickBottomWidgetButton();
    this.assertDocumentExists("Other Leaves - current version");
    return this;
  }

  /**
   * Fills accrued leave fields within the "Other Leaves - current version" eForm
   * You can currently submit only 1 accrued paid leave.
   * @param leave
   * @param i
   */
  private fillAccruedLeaveData(leave: ValidConcurrentLeave) {
    // If there's an accrued leave - we just say yes.
    cy.findByLabelText(
      "Will you use any employer-sponsored accrued paid leave for a qualifying reason during this leave?"
    ).select("Yes");
    cy.findByLabelText(
      "Will you use accrued paid leave from this employer?"
    ).select(leave.is_for_current_employer ? "Yes" : "No");
    cy.get(`input[type=text][id$=AccruedStartDate1]`).type(
      `${dateToMMddyyyy(leave.leave_start_date)}{enter}`
    );
    cy.get(`input[type=text][id$=AccruedEndDate1]`).type(
      `${dateToMMddyyyy(leave.leave_end_date)}{enter}`
    );
    cy.wait("@ajaxRender").wait(200);
  }

  /**
   * Fills previous leave fields within the "Other Leaves - current version" eForm
   * @param leave
   * @param i
   */
  private fillPreviousLeaveData(leave: ValidPreviousLeave, i: number) {
    // Increment this, because the selectors within the form start from 1
    i += 1;
    const leaveReasonMap: Record<ValidPreviousLeave["leave_reason"], string> = {
      Pregnancy: "Pregnancy",
      "An illness or injury": "An illness or injury",
      "Caring for a family member with a serious health condition":
        "Caring for a family member with a serious health condition",
      "Bonding with my child after birth or placement":
        "Bonding with my child after birth or placement",
      "Caring for a family member who serves in the armed forces":
        "Caring for a family member who serves in the armed forces",
      "Managing family affairs while a family member is on active duty in the armed forces":
        "Managing family affairs while a family member is on active duty in the armed forces",
      Unknown: "Please select",
    };

    /*
    Because the labels are the same for every leave you report, we have to get creative with selectors
    Each input has a unique id, with the number of leave being reported attached at the end.
    */
    //  Did you take any other leave between January 1, 2021 and the first day of the leave you're requesting for the same reason or a different qualifying reason as the leave you're requesting?
    cy.get(`select[id$=V2Applies${i}]`).select("Yes");
    // Was the leave for the same reason as you are applying for paid leave now?
    const isForSameReason = {
      same_reason: "Yes",
      other_reason: "No",
      deprecated: "Please Select",
    };
    // The eForm also doesn't require you to fill anything at all, and can be submitted essentially empty.
    // So we only fill in the data we were given.

    cy.get(`select[id$=V2Leave${i}]`).select(isForSameReason[leave.type]);
    // Why did you need to take leave?

    cy.get(`select[id$=QualifyingReason${i}]`).select(
      leaveReasonMap[leave.leave_reason]
    );
    // Did you take this leave from the same employer as the one you're applying to take paid leave from now?

    cy.get(`select[id$=LeaveFromEmployer${i}]`).select(
      leave.is_for_current_employer ? "Yes" : "No"
    );

    // What was the first day of this leave?

    cy.get(`input[type=text][id$=OtherLeavesPastLeaveStartDate${i}]`).type(
      `${dateToMMddyyyy(leave.leave_start_date)}{enter}`
    );
    // What was the last day of this leave?

    cy.get(`input[type=text][id$=OtherLeavesPastLeaveEndDate${i}]`).type(
      `${dateToMMddyyyy(leave.leave_end_date)}{enter}`
    );

    // How many hours did you work per week on average at the time you took this leave?

    const [hoursWorked, minutesWorked] = minutesToHoursAndMinutes(
      leave.worked_per_week_minutes
    );
    cy.get(`input[type=text][id$=HoursWorked${i}]`).type(
      `{selectall}{backspace}${hoursWorked}`
    );
    cy.get(`select[id$=MinutesWorked${i}]`).select(
      `${minutesWorked === 0 ? "00" : minutesWorked}`
    );

    // What was the total number of hours you took off?

    const [hoursTotal, minutesTotal] = minutesToHoursAndMinutes(
      leave.leave_minutes
    );
    cy.get(`input[type=text][id$=TotalHours${i}]`).type(
      `{selectall}{backspace}${hoursTotal}`
    );
    cy.get(`select[id$=TotalMinutes${i}]`).select(
      `${minutesTotal === 0 ? "00" : minutesTotal}`
    );
  }

  adjustDocumentStatus(notice: string, status: string): this {
    cy.get(
      'table[id^="DocumentsForCaseListviewWidget_"][id$="_DocumentsViewControl"]'
    )
      .contains("tr", notice)
      .click()
      .should("have.class", "ListRowSelected");
    // Open document properties
    cy.findByTitle("Document Properties").click();
    cy.get("span[id^='DocumentPropertiesWidget']")
      .find("select[id$='status']")
      .select(status);
    fineos.clickBottomWidgetButton("OK");
    return this;
  }

  checkDocumentFileExtension(notice: string, fileExtension: RegExp): this {
    cy.get(
      'table[id^="DocumentsForCaseListviewWidget_"][id$="_DocumentsViewControl"]'
    )
      .contains("tr", notice)
      .click()
      .should("have.class", "ListRowSelected");
    // Open document properties
    cy.findByTitle("Document Properties").click();
    cy.get("span[id='DocumentPropertiesWidget']")
      .find("span[id$='fileName']")
      .invoke("text")
      .should("match", fileExtension);
    fineos.clickBottomWidgetButton("OK");
    return this;
  }
}

/**
 * This class represents the alerts page/tab within the broader Claim page/view in Fineos.
 */
export class AlertsPage {
  assertAlertMessage(hasMessage: boolean, alertMessage: string): this {
    if (hasMessage) {
      cy.get(`#alertsHeader`).should((alerts) => {
        expect(
          alerts,
          `Expected to find the following "${alertMessage}".`
        ).to.have.descendants(`:contains("${alertMessage}")`);
      });
    } else {
      cy.get(
        `table[id^="ValidationsListViewWidget_"][id$="_ValidationList"]`
      ).should("not.be.visible");
    }
    return this;
  }
}

class AvailabilityPage {
  reevaluateAvailability(decision: string, reason: string) {
    waitForAjaxComplete();
    cy.get('input[title="Manage time for the selected Leave Plan"]').click();
    waitForAjaxComplete();
    cy.get('input[title="Select All"]').click();
    waitForAjaxComplete();
    // findByLabelText() wont work here - labels do not have the "for" or "aria-labelledby" attributes
    cy.contains("label", "Decision")
      .parent()
      .parent()
      .within(() => {
        cy.get("select").select(decision);
      });
    waitForAjaxComplete();
    cy.contains("label", "Reason")
      .parent()
      .parent()
      .within(() => {
        cy.get("select").select(reason);
      });
    cy.get('input[type="submit"][value="Apply"]').click();
    cy.get("#footerButtonsBar").within(() => {
      cy.findByText("Close").click({ force: true });
    });
  }

  assertDailyWeight(amount_weeks: string, upgrade: boolean): this {
    if (upgrade) {
      cy.contains(".ant-table-wrapper .ant-table-container", "Weight");
      const selector =
        ".ant-table-wrapper .ant-table-container .ant-table-body td:nth-child(12)";
      cy.get(selector).should("contain.text", amount_weeks);
    } else {
      cy.contains("table.ListTable", "Weight");
      const selector =
        ".divListviewGrid .ListTable td[id*='ListviewWidgetWeight0']";
      cy.get(selector).should("contain.text", amount_weeks);
    }
    cy.screenshot();
    fineos.clickBottomWidgetButton("Close");
    return this;
  }
}

class PaidBenefitsPage {
  assertSitFitOptIn(isParticipating: boolean): this {
    cy.contains("td[id*='SIT/FIT Opt In']", isParticipating ? "true" : "false");
    return this;
  }

  assertAutoPayStatus(assertValue: boolean): this {
    cy.get("td[id*='AutoApproveProcessPayment']").then((td) => {
      expect(td).to.have.text(assertValue ? "Yes" : "No");
    });
    return this;
  }

  edit(): this {
    cy.get("input[type='submit'][value='Edit']").click();
    return this;
  }
}

const reductionCategories = {
  ["Accrued paid leave" as const]: "",
  ["Earnings from another employment/self-employment" as const]: "",
  ["Family or medical leave insurance" as const]: "",
  ["Jones Act benefits" as const]: "",
  ["Permanent disability insurance" as const]: "",
  ["Temporary disability insurance" as const]: "",
  ["Unemployment Insurance" as const]: "",
};

type PaidLeaveDocumentStatus = "Unknown" | "Completed" | "Draft";

class PaidLeaveDocumentPropertiesPage {
  fileNameShouldMatch(re: RegExp): PaidLeaveDocumentsPage {
    cy.get("span[id='DocumentPropertiesWidget']")
      .find("span[id$='fileName']")
      .invoke("text")
      .should("match", re);

    fineos.clickBottomWidgetButton("OK");

    return new PaidLeaveDocumentsPage();
  }

  setStatus(status: PaidLeaveDocumentStatus): PaidLeaveDocumentsPage {
    cy.get("span[id^='DocumentPropertiesWidget']")
      .find("select[id$='status']")
      .select(status);

    fineos.clickBottomWidgetButton("OK");

    return new PaidLeaveDocumentsPage();
  }
}

class PaidLeaveDocumentsPage {
  assertDocumentExists(documentName: string): this {
    assertHasDocument(documentName);
    return this;
  }

  /**
   * @param document - the name of the desired document
   * @param cb - actions to take on the desired document's properties page
   * @returns whatever `cb` returns
   */
  properties<T>(
    document: string,
    cb: (page: PaidLeaveDocumentPropertiesPage) => T
  ): T {
    cy.get("table[id*='DocumentsForCaseListviewWidget'] tbody")
      .contains("tr", document)
      .click();
    cy.get("input[id$='DocumentProperties']").click();

    waitForAjaxComplete();

    return cb(new PaidLeaveDocumentPropertiesPage());
  }
}

/**
 * Future or made payment.
 */
type Payment = {
  net_payment_amount: number;
  paymentInstances?: number;
  paymentProcessingDates?: Date[];
};

/**
 * Data needed to apply a reduction to a payment in a paid leave case.
 */
type Reduction = {
  type: keyof typeof reductionCategories;
  start_date: string;
  end_date: string;
  frequency_same_as_due: boolean;
  amount: number;
};

type PaidLeaveCorrespondenceDocument =
  | "Benefit Amount Change Notice"
  | "Maximum Weekly Benefit Change Notice"
  | "Overpayment Notice - Full Balance Recovery";

type PendingAmount = Record<
  "netAmount" | "netPaymentAmount" | "processingDate",
  string
>;

/**
 * Class representing the Absence Paid Leave Case,
 * Claim should be adjudicated and approved before trying to access this.
 */
class PaidLeavePage {
  private activeTab: string;

  constructor() {
    this.activeTab = "General Claim";
  }

  private onTab(...path: string[]) {
    if (this.activeTab !== path.join(",")) {
      for (const part of path) {
        onTab(part);
      }
      this.activeTab = path.join(",");
    }
  }

  tasks(cb: (page: TasksPage) => unknown): this {
    onTab("Tasks");
    cb(new TasksPage());
    onTab("General Claim");
    return this;
  }

  FinancialsBenefitAdjustmentsPage(
    cb: (page: FinancialsBenefitAdjustmentsPage) => unknown
  ): this {
    this.onTab(
      "Financials",
      "Recurring Payments",
      "Benefit Amount and Adjustments"
    );
    cb(new FinancialsBenefitAdjustmentsPage());
    onTab("General Claim");
    return this;
  }

  /**
   * Applies reductions to the paid leave case based on reported other incomes & benefits.
   */
  applyReductions({
    other_incomes,
    employer_benefits,
  }: {
    other_incomes?: NonEmptyArray<ValidOtherIncome>;
    employer_benefits?: NonEmptyArray<ValidEmployerBenefit>;
  }): this {
    // Go to the right tab
    this.onTab(
      "Financials",
      "Recurring Payments",
      "Benefit Amount and Adjustments"
    );
    cy.contains(
      `input[name^="BenefitAmountOffsetsAndDeductions"]`,
      "Add"
    ).click();
    const incomesAndBenefits: (ValidOtherIncome | ValidEmployerBenefit)[] = [];
    if (other_incomes) incomesAndBenefits.push(...other_incomes);
    if (employer_benefits) incomesAndBenefits.push(...employer_benefits);
    // Get reductions from the other incomes & benefits data.
    const reductions = incomesAndBenefits
      .map(this.getReduction)
      .filter((el) => isNotNull(el));

    (reductions as Reduction[]).forEach((reduction) => {
      this.applyReduction(reduction);
    });

    clickBottomWidgetButton();
    return this;
  }

  createCorrespondenceDocument(
    document: PaidLeaveCorrespondenceDocument
  ): this {
    cy.get("a[id$=Correspondencelink]")
      .click({ scrollBehavior: false })
      .parents("li")
      .findByText(document)
      .click({ scrollBehavior: false });

    waitForAjaxComplete();

    cy.get("span[id='footerButtonsBar']").find("input[id$='next']").click();

    return this;
  }

  triggerPaidLeaveNotice(type: PaidLeaveCorrespondenceDocument): this {
    this.onTab("Tasks", "Processes");

    cy.contains(".TreeNodeElement", type).click({
      force: true,
    });
    waitForAjaxComplete();
    // When we're firing time triggers, there's always the possibility that the trigger has already happened
    // by the time we get here. When this happens, the "Properties" button will be grayed out and unclickable.
    cy.get('input[type="submit"][value="Properties"]').then((el) => {
      if (el.is(":disabled")) {
        cy.log("Skipping trigger because this time trigger has already fired");
        return;
      }
      cy.wrap(el).click();

      waitForAjaxComplete();

      cy.get("span[id='ProcessPropertiesWidget']")
        .find("input[id$='ContinueButton']")
        .click();
    });

    this.onTab("General Claim");
    return this;
  }

  documents(cb: (page: PaidLeaveDocumentsPage) => unknown): this {
    this.onTab("Documents");
    cb(new PaidLeaveDocumentsPage());
    this.onTab("General Claim");
    return this;
  }

  /**
   * Maps incomes and benefits to available reduction types.
   * @param incomeOrBenefit a valid OtherIncome or EmployerBenefit data object.
   * @returns reduction data for a given income or benefit.
   */
  private getReduction(
    incomeOrBenefit: ValidOtherIncome | ValidEmployerBenefit
  ): Reduction | null {
    /**
     * Some income & benefit types either won't or are unlikely to generate a reduction.
     * For more in-depth discussion, look at {@link https://teams.microsoft.com/l/message/19:1d317494c5204955a5516be9cd408ab3@thread.skype/1623770851214?tenantId=3e861d16-48b7-4a0e-9806-8c04d81b7b2a&groupId=f2159e94-1fdd-4834-b5c1-79578a664392&parentMessageId=1623748456804&teamName=EOL-PFMLProject&channelName=Claims%20Processing%20System&createdTime=1623770851214 this Teams thread}
     */
    const reductionTypeMap: Record<
      ValidEmployerBenefit["benefit_type"] | ValidOtherIncome["income_type"],
      Reduction["type"] | "None"
    > = {
      "Accrued paid leave": "Accrued paid leave",
      "Earnings from another employment/self-employment":
        "Earnings from another employment/self-employment",
      "Family or medical leave insurance": "Family or medical leave insurance",
      "Jones Act benefits": "Jones Act benefits",
      "Permanent disability insurance": "Permanent disability insurance",
      "Short-term disability insurance": "Temporary disability insurance",
      "Unemployment Insurance": "Unemployment Insurance",

      "Disability benefits under Gov't retirement plan": "None",
      "Railroad Retirement benefits": "None",
      "Workers Compensation": "None",
      SSDI: "None",
      Unknown: "None",
    } as const;
    if (isValidOtherIncome(incomeOrBenefit)) {
      const reductionType = reductionTypeMap[incomeOrBenefit.income_type];
      if (reductionType === "None") return null;
      return {
        type: reductionType,
        amount: incomeOrBenefit.income_amount_dollars,
        start_date: incomeOrBenefit.income_start_date,
        end_date: incomeOrBenefit.income_end_date,
        frequency_same_as_due: true,
      };
    } else {
      const reductionType = reductionTypeMap[incomeOrBenefit.benefit_type];
      if (reductionType === "None") return null;
      return {
        type: reductionType,
        amount: incomeOrBenefit.benefit_amount_dollars,
        start_date: incomeOrBenefit.benefit_start_date,
        end_date: incomeOrBenefit.benefit_end_date,
        frequency_same_as_due: true,
      };
    }
  }

  /**
   * Adds a given reduction to the paid leave case.
   * Assumes being navigated to "Add Benefit Amount" page.
   * @param reduction
   * @param index
   */
  private applyReduction({ type, start_date, end_date, amount }: Reduction) {
    // Select the type of reduction.
    cy.findByText(type).click();

    // Fill in the dates.
    cy.findByLabelText("Start Date")
      .focus()
      .type(`${dateToMMddyyyy(start_date)}{enter}`);

    waitForAjaxComplete();
    cy.findByLabelText("Start Date").focus().should("have.focus");

    cy.findByLabelText("End Date")
      .focus()
      .type(`${dateToMMddyyyy(end_date)}{enter}`);
    cy.findByLabelText("End Date").should("have.focus");

    // Fill in the income/benefit amount. The label for this field isn't connected so we have to use a more direct selector.
    cy.get("input[type=text][id$=adjustmentAmountMoney]").type(
      `{selectAll}{backspace}${amount}`
    );
    // Add the reduction
    cy.findByDisplayValue("Add").click();

    // Check the reduction has been added.
    cy.contains("table", "Benefit Adjustments").within(() => {
      cy.findByText(type).should("contain.text", type);
      cy.findByText(`-${numToPaymentFormat(amount)}`).should(
        "contain.text",
        `-${numToPaymentFormat(amount)}`
      );
    });
  }

  /**
   * Asserts there are pending payments for a given amount. Assertion for payment dates are also supported.
   * Assertions for payment amounts and dates disregard payment ordering, which can sometimes vary by environment
   * @param amountsPending array of expected pending payments.
   * @returns
   */
  assertAmountsPending(amountsPending: Payment[]): this {
    this.onTab("Financials", "Payment History", "Amounts Pending");
    if (!amountsPending.length) return this;
    cy.contains("table.WidgetPanel", "Amounts Pending")
      // Get the table
      .find("table.ListTable")
      .within(() => {
        amountsPending.forEach((payment) => {
          if (payment.net_payment_amount) {
            // find row items that contain payment information
            cy.get(`tbody tr`).within(() => {
              // get all row items that contain a matching net payment amouns
              cy.get(
                `td:nth-child(8):contains(${numToPaymentFormat(
                  payment.net_payment_amount
                )})`
              )
                .parent()
                .then((paymentRows) => {
                  // validate the correct amount of payments appear for each payment amount.
                  expect(paymentRows.length).to.equal(
                    payment.paymentInstances ?? 1,
                    `Expected ${payment.paymentInstances ?? 1} payment(s) of ${
                      payment.net_payment_amount
                    } - received ${paymentRows.length} instances`
                  );
                  if (payment.paymentProcessingDates) {
                    // grab payment process date column text from payment row
                    const actualProcessingDates = [...paymentRows].map(
                      (el) => el.children[2].textContent
                    );
                    for (const expectedDate of payment.paymentProcessingDates) {
                      const index = actualProcessingDates.findIndex(
                        (date) => format(expectedDate, "MM/dd/yyyy") === date
                      );
                      expect(index).gt(
                        -1,
                        `Expected to find payment date of ${format(
                          expectedDate,
                          "MM/dd/yyyy"
                        )} for payment amount ${numToPaymentFormat(
                          payment.net_payment_amount
                        )}`
                      );
                      // removing previously matched payment dates prevents a false prositive from occurring
                      actualProcessingDates.splice(index, 1);
                    }
                  }
                });
            });
          }
        });
      });
    return this;
  }

  /**
   * Asserts there are payments made for a given amount.
   * @param paymentsMade array of expected made payments.
   * @returns
   */
  assertPaymentsMade(paymentsMade: Payment[]): this {
    if (!paymentsMade.length) return this;
    this.onTab("Financials", "Payment History", "Payments Made");
    cy.contains("table.WidgetPanel", "Payments Made")
      .find("table.ListTable")
      .within(() => {
        paymentsMade.forEach((payment, i) => {
          // Note: We don't want to rely on row classes here, as they are added an indeterminate time after the page is
          // rendered.
          cy.get(`tr:nth-child(${i + 1})`).should(
            "contain.text",
            numToPaymentFormat(payment.net_payment_amount)
          );
        });
      });
    return this;
  }

  /**
   * Asserts there are alotted payments for a given amount.
   * @param allotedPayments array of expected alotted payments.
   */
  assertPaymentAllocations(allotedPayments: Payment[]): this {
    if (!allotedPayments.length) return this;
    this.onTab("Financials", "Payment History", "Payments Made");
    cy.contains("table.WidgetPanel", "Payment Allocations").within(() => {
      const [first, ...rest] = allotedPayments;
      // Get and assert contents of the the first row. It has a unique selector.
      cy.get("tr.ListRowSelected").should(
        "contain.text",
        first.net_payment_amount.toFixed(2)
      );
      // Get and assert contents of the the other rows if present.
      rest.forEach((payment, i) => {
        cy.get(`tr.ListRow${i + 2}`).should(
          "contain.text",
          numToPaymentFormat(payment.net_payment_amount)
        );
      });
    });
    return this;
  }

  assertPaymentAddress(address: Address): this {
    this.onTab("Financials", "Recurring Payments", "Payment Details");
    cy.get("span[id*='PaymentAddress']").should((span) => {
      if (address.line_1) expect(span).to.contain.text(address.line_1);
      if (address.line_2) expect(span).to.contain.text(address.line_2);
      if (address.city) expect(span).to.contain.text(address.city);
      if (address.state) expect(span).to.contain.text(address.state);
      if (address.zip) expect(span).to.contain.text(address.zip);
    });
    return this;
  }

  assertPaymentPreference({
    payment_preference,
  }: PaymentPreferenceRequestBody): this {
    if (!payment_preference) throw new Error("No payment preference given");
    if (payment_preference.payment_method !== "Elec Funds Transfer")
      throw new Error(
        "Assertions on payment preferences other than EFT are not implemented yet."
      );

    this.onTab("Financials", "Recurring Payments", "Payment Details");
    // The "Expand" button seems to show inconsistently. Only try to click expand if we see an expand button.
    cy.get("#PayeeWidget > .WidgetPanel").then((panel) =>
      panel.find("[title='Expand this Section']").each((i, el) => {
        cy.wrap(el).click();
      })
    );
    cy.get("[id*='paymentMethodDropDown']").should(
      "contain.text",
      payment_preference.payment_method
    );
    cy.get("[id*='bankAccountNo']").should(
      "contain.text",
      payment_preference.account_number
    );
    cy.get("[id*='routingNumber']").should(
      "contain.text",
      payment_preference.routing_number
    );

    return this;
  }

  assertAutoPayStatus(assertValue: boolean): this {
    this.onTab("Financials", "Recurring Payments", "Payment Details");
    cy.get("input[value='Edit']").click();
    waitForAjaxComplete();
    cy.get("input[type='checkbox'][name*='AutoPay_CHECKBOX']").should(
      assertValue ? "be.checked" : "not.be.checked"
    );
    clickBottomWidgetButton("Cancel");
    return this;
  }

  changeAutoPayStatus(value: boolean): this {
    this.onTab("Financials", "Recurring Payments", "Payment Details");
    cy.get("input[value='Edit']").click();
    waitForAjaxComplete();
    if (value) {
      cy.get("input[type='checkbox'][name*='AutoPay_CHECKBOX']").check();
    } else {
      cy.get("input[type='checkbox'][name*='AutoPay_CHECKBOX']").uncheck();
    }
    clickBottomWidgetButton();
    return this;
  }

  approvePeriod(): this {
    this.onTab("Financials", "Recurring Payments", "Periods");
    cy.get("input[value='Edit']").click();
    waitForAjaxComplete();
    cy.findByLabelText("Status").select("Approved");
    clickBottomWidgetButton();
    return this;
  }

  /**
   *  Asserts processing and end dates match.
   */
  assertMatchingPaymentDates(): this {
    this.onTab("Financials", "Payment History", "Amounts Pending");
    cy.contains("table.WidgetPanel", "Amounts Pending").within(() => {
      cy.get('td[id*="processing_date0"]')
        .invoke("text")
        .then((processingDate) => {
          cy.get('td[id*="period_end_date0"]')
            .invoke("text")
            .should("eq", processingDate);
        });
    });
    return this;
  }

  assertOwnershipAssignTo(assign: string): this {
    this.onTab("General Claim");
    cy.get('span[id*="AssignedTo"]').should((element) => {
      expect(
        element,
        `Expected the Assigned To display the following "${assign}"`
      ).to.have.text(assign);
    });
    return this;
  }

  /**
   * Modifies payment processing date for the first payment under amounts pending.
   * @param date - Optional date to set payment for payment processing. Defaults to new Date()
   * @returns PaidLeavePage
   */
  editPaymentProcessingDate(date = new Date()): this {
    this.onTab("Financials", "Payment History", "Amounts Pending");
    waitForAjaxComplete();
    cy.get('input[type="submit"][value="Edit"]').click();
    waitForAjaxComplete();
    cy.get(
      'input[type="checkbox"][id$="overrideprocessingdate_CHECKBOX"]'
    ).click({ force: true });
    waitForAjaxComplete();
    cy.wait(350);
    cy.get('input[type="text"][id$="processingDate"]').type(
      `{selectAll}{backspace}${format(date, "MM/dd/yyyy")}`,
      { force: true }
    );
    clickBottomWidgetButton();
    // confirm that payment processing date has been changed
    cy.get(`td:nth-child(3):contains(${format(date, "MM/dd/yyyy")})`);
    return this;
  }

  assertOverpaymentRecord(overpayments: OverpaymentRecord) {
    this.onTab("Financials", "Payment History", "Overpayment Summary");
    cy.get("table[id$='OverpaymentsListview']").within(() => {
      cy.contains("td[id$='OverpaymentsListviewStatus0']", overpayments.status);
      cy.contains(
        "td[id$='OverpaymentsListviewBalancingAmount0']",
        numToPaymentFormat(overpayments.amount)
      );
      cy.contains(
        "td[id$='OverpaymentsListviewOverpaymentRecordAdjustment0']",
        numToPaymentFormat(overpayments.adjustment)
      );
      cy.contains(
        "td[id$='OverpaymentsListviewOutstandingAmount0']",
        numToPaymentFormat(overpayments.outstandingAmount)
      );
    });
  }

  createRecoveryPlan(
    recoveryAmt: number,
    type: "OffsetRecovery" | "Reimbursement"
  ): RecoveryPlanPage {
    this.onTab("Financials", "Payment History", "Overpayment Summary");
    waitForAjaxComplete();
    cy.get("tr[class='ListRowSelected']").click({ force: true });
    waitForAjaxComplete();
    cy.get('input[type="submit"][value="Open"]').click({ force: true });
    cy.get(
      'input[type="submit"][value="Add"][id^="RecoveryPlanListviewWidget"]'
    ).click();
    waitForAjaxComplete();
    cy.findByLabelText("Type").select(type);
    waitForAjaxComplete();
    cy.wait(500);
    cy.findByLabelText("Agreement Date").type(
      `${format(new Date(), "MM/dd/yyyy")}{enter}`
    );
    waitForAjaxComplete();
    cy.wait(500);
    if (type === "Reimbursement") {
      cy.get("input[type='text'][name$='Amount_to_Submit']").type(
        `{selectAll}{backspace}${numToPaymentFormat(recoveryAmt)}`
      );
    }
    if (type === "OffsetRecovery") {
      cy.get("input[type='text'][name$='Amount_per_Frequency']").type(
        `{selectAll}{backspace}${numToPaymentFormat(recoveryAmt)}`
      );
      waitForAjaxComplete();
      cy.get(
        "input[type='submit'][id$='calculateEstimatedOffsetEndDate']"
      ).click();
    }
    waitForAjaxComplete();
    clickBottomWidgetButton();
    waitForAjaxComplete();
    return new RecoveryPlanPage();
  }

  getAmountsPending(): Cypress.Chainable<PendingAmount[]> {
    this.onTab("Financials", "Payment History", "Amounts Pending");
    waitForAjaxComplete();
    // net amount
    return cy.get("td[id$='benefit_amount_money0']").then(([...netPymt]) => {
      // net payment amount
      return cy.get("td[id$='payment_amount_money0']").then((netPymtCols) => {
        return cy.get("td[id$='processing_date0']").then((processingDates) => {
          return cy.wrap(
            [...netPymtCols].reduce((acc, netPaymentAmountCol, idx) => {
              const rowData = {
                netAmount: netPymt[idx].textContent as string,
                netPaymentAmount: netPaymentAmountCol.textContent as string,
                processingDate: processingDates[idx].textContent as string,
              };
              acc.push(rowData);
              return acc;
            }, [] as PendingAmount[])
          );
        });
      });
    });
  }
  goToOverpaymentCase(): RecoveryPlanPage {
    this.onTab("Financials", "Payment History", "Overpayment Summary");
    waitForAjaxComplete();
    cy.get("tr[class='ListRowSelected']").click({ force: true });
    waitForAjaxComplete();
    cy.get('input[type="submit"][value="Open"]').click({ force: true });
    waitForAjaxComplete();
    return new RecoveryPlanPage();
  }
}

type OverpaymentRecord = {
  status: string;
  amount: number;
  adjustment: number;
  outstandingAmount: number;
};

type RecoveryPageCorrespondenceDropdownOptions =
  | "OP-Full Balance Demand"
  | "OP-Full Balance Recovery"
  | "OP-Full Balance Recovery-Manual"
  | "OP-Notice of Payoff"
  | "OP-Payment Received";

type RecoveryPlanDocuments =
  | "Overpayment Notice-Full Balance Recovery"
  | "Overpayment Notice-Full Balance Recovery-Manual"
  | "Overpayment Notice-Full Balance Demand"
  | "Overpayment Payoff Notice"
  | "Payment Received-Updated Overpayment Balance";

class RecoveryPlanPage {
  addDocument(
    correspondenceOption: RecoveryPageCorrespondenceDropdownOptions,
    documentType: RecoveryPlanDocuments
  ): this {
    cy.contains("a", "Correspondence").click({ force: true });
    waitForAjaxComplete();
    cy.contains(correspondenceOption).click();
    clickBottomWidgetButton("Next");
    onTab("Documents");
    assertHasDocument(documentType);
    return this;
  }
  assertDocumentStatus(
    documentType: RecoveryPlanDocuments,
    status: PaidLeaveDocumentStatus
  ) {
    onTab("Documents");
    waitForAjaxComplete();
    cy.contains("tr", documentType).within(() => {
      cy.contains("td", status);
    });
  }
  addActualRecovery(recoveryAmt: number): this {
    cy.get(
      "input[type='submit'][value='Add'][name^='ActualRecoveriesListviewWidget']"
    ).click({ force: true });
    waitForAjaxComplete();
    cy.findByLabelText("Amount of Recovery").type(
      `{selectAll}{backspace}${numToPaymentFormat(recoveryAmt)}`
    );
    waitForAjaxComplete();
    cy.findByLabelText("Check Number").type("5555");
    clickBottomWidgetButton();
    waitForAjaxComplete();
    return this;
  }
  assertTaskExists(name: FineosTasks): this {
    onTab("Tasks");
    waitForAjaxComplete();
    cy.get("table[id*='TasksForCaseWidget']").should((table) => {
      expect(table, `Expected to find a "${name}" task`).to.have.descendants(
        `tr td:nth-child(6)[title="${name}"]`
      );
    });
    return this;
  }
  assertOutstandingOverpaymentBalance(amount: number): this {
    onTab("Recovery Details");
    waitForAjaxComplete();
    cy.contains("span[id$=OutstandingAmount]", numToPaymentFormat(amount));
    return this;
  }
}

export function numToPaymentFormat(num: number): string {
  const decimal = num % 1 ? "" : ".00";
  return `${new Intl.NumberFormat("en-US", {
    style: "decimal",
  }).format(num)}${decimal}`;
}

/**
 * Function to determine payment processing dates when preventing overpayments.
 * Note: This is intended to be used for this specific scenario, and won't be compatible with every payment under Amounts Pending
 * Read more on preventing overpayments here: https://lwd.atlassian.net/browse/CPS-3115
 * @returns Date
 */
export function calculatePaymentDatePreventingOP(
  approvalDate?: Date,
  considerEST = true
) {
  const PFML_HOLIDAYS = [
    "2022-02-21",
    "2022-04-18",
    "2022-05-30",
    "2022-06-20",
    "2022-07-04",
    "2022-09-05",
    "2022-10-10",
    "2022-11-11",
    "2022-11-24",
    "2022-12-26",
    "2023-01-02",
    "2023-01-16",
    "2023-02-20",
    "2023-04-17",
    "2023-05-29",
    "2023-06-19",
    "2023-07-04",
    "2023-09-04",
    "2023-10-09",
    "2023-11-23",
    "2023-12-25",
  ] as const;
  const estTimeHour = getHours(
    convertToTimeZone(new Date(), {
      timeZone: "America/New_York",
    })
  );
  const isBeforeEndBusinessDay = estTimeHour < 17;

  // Determines if EST time should be used to determine if an extra day should be applied to the Date returned by calculatePaymentDatePreventingOP
  const considerBusinessDay = () => {
    if (considerEST) {
      return addBusinessDays(
        approvalDate ?? new Date(),
        isBeforeEndBusinessDay ? 5 : 6
      );
    } else return addBusinessDays(approvalDate ?? new Date(), 5);
  };

  const hasHoliday = (holiday: Date) => {
    return (
      isAfter(holiday, subDays(new Date(), 1)) &&
      isBefore(holiday, addDays(considerBusinessDay(), 1))
    );
  };
  // account for holidays - which further delays the payment processing date
  let totalHolidays = 0;
  for (let i = 0; i < PFML_HOLIDAYS.length; i++) {
    if (hasHoliday(parseISO(PFML_HOLIDAYS[i]))) totalHolidays += 1;
  }
  return addBusinessDays(considerBusinessDay(), totalHolidays);
}

class BenefitsExtensionPage {
  private continue(text = "Next") {
    clickBottomWidgetButton(text);
    waitForAjaxComplete();
  }

  private enterExtensionLeaveDates(
    newStartDate: string,
    newEndDate: string,
    workPattern: "continuous" | "reduced"
  ) {
    cy.findByLabelText("Absence status").select("Known");
    cy.get("input[id$='_startDate']").type(
      `{selectall}{backspace}${newStartDate}{enter}`
    );
    cy.wait("@ajaxRender");
    cy.wait(200);
    cy.get("input[id$='_endDate']").type(
      `{selectall}{backspace}${newEndDate}{enter}`
    );
    cy.wait("@ajaxRender");
    cy.wait(200);
    if (workPattern === "continuous") {
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
    } else {
      cy.get("input[id^=hoursPerDayDetailsWidget][id$='hours']").each(
        ($el, index, $list) => {
          if (index !== 0 && index != $list.length - 1) {
            cy.wrap($el).type("4");
          }
        }
      );
    }
    cy.get("input[title='OK']").click();
  }

  extendLeave(
    newStartDate: string,
    newEndDate: string,
    anotherReason = false,
    workPattern: "continuous" | "reduced" = "continuous"
  ): this {
    onTab("Capture Additional Time");
    if (anotherReason) {
      cy.get('input[type="radio"][value*="another_reason_id"]').click();
      waitForAjaxComplete();
    }
    const addTimeButtonTitles = {
      continuous: "Add Time Off Period",
      reduced: "Add Reduced Schedule Period",
    } as const;
    cy.findByTitle(addTimeButtonTitles[workPattern]).click();
    // This assumes the claim is continuos
    this.enterExtensionLeaveDates(newStartDate, newEndDate, workPattern);
    this.continue();
    this.continue();
    this.continue();
    this.continue();
    this.continue("OK");
    anotherReason && this.assertAddedOtherLeave();
    return this;
  }

  private assertAddedOtherLeave(): void {
    // Assert bonding leave request was added
    cy.get("[id*='processPhaseEnum']").should("contain.text", "Adjudication");
    cy.get("[id*='requestedLeaveCardWidget']")
      .parent()
      .within(() => {
        cy.contains("Pending leave");
        cy.contains(/(Fixed time off|Reduced schedule) for Child Bonding/);
      });
  }
}

export class FinancialsBenefitAdjustmentsPage {
  addEmployerReimbursement(
    benefit_start_date: string,
    benefit_end_date: string,
    amount_to_employer: number
  ): this {
    const type = "Employer Reimbursement";

    cy.contains(
      `input[name^="BalancedPayeeOffsetsAndDeductions"]`,
      "Add"
    ).click();

    this.addAdjustment(
      type,
      benefit_start_date,
      benefit_end_date,
      amount_to_employer
    );
    this.validatePayeeAdjustmentAdded(type, amount_to_employer);
    clickBottomWidgetButton();

    // Check the Employer Reimbursement has been added
    cy.contains("table", "Balanced Payee Adjustments").within(() => {
      cy.findByText(type).should("contain.text", type);
      cy.findByText(`-${numToPaymentFormat(amount_to_employer)}`).should(
        "contain.text",
        `-${numToPaymentFormat(amount_to_employer)}`
      );
    });
    return this;
  }

  editAutoGrossEntitlementAmount(adjust_by_amount: number) {
    const type = "Auto Gross Entitlement";

    cy.get("[id*='BenefitAmountsRecurringListviewWidgetAbsence']")
      .contains(type)
      .click();
    waitForAjaxComplete();
    cy.get("[id*='BenefitAmountsRecurringListviewWidgetAbsence']")
      .contains(type)
      .siblings(`[id*="OffsetsAndDeductionsAmount"]`)
      .invoke("text")
      .then((value) => {
        const current_ammount = parseFloat(value.replace(/[^0-9.]/g, ""));
        cy.contains(
          `input[name^="BenefitAmountOffsetsAndDeductionsListView"]`,
          "Edit"
        ).click();

        const new_amount = current_ammount + adjust_by_amount;
        this.editAdjustment(new_amount, null, null);
        waitForAjaxComplete();

        cy.get("[id*='BenefitAmountsRecurringListviewWidgetAbsence']")
          .contains(type)
          .siblings(`[id*="OffsetsAndDeductionsAmount"]`)
          .should("contain.text", `${numToPaymentFormat(new_amount)}`);
      });
  }

  private addAdjustment(
    type: string,
    start_date: string,
    end_date: string,
    amount: number
  ) {
    // Select the type of reduction.
    cy.get("table[id^='SelectAutoIncreaseOptionListviewWidget'")
      .findByText(type)
      .click();
    waitForAjaxComplete();

    // Fill in the dates.
    cy.findByLabelText("Start Date")
      .focus()
      .type(`${dateToMMddyyyy(start_date)}{enter}`);
    cy.findByLabelText("Start Date").focus().should("have.focus");

    cy.findByLabelText("End Date")
      .focus()
      .type(`${dateToMMddyyyy(end_date)}{enter}`);
    cy.findByLabelText("End Date").should("have.focus");

    // Fill in the income/benefit amount. The label for this field isn't connected so we have to use a more direct selector.
    cy.get("input[type=text][id$=adjustmentAmountMoney]").type(
      `{selectAll}{backspace}${amount}`
    );
    // Add the reduction
    cy.findByDisplayValue("Add").click();
  }

  private editAdjustment(
    amount: number | null,
    start_date: string | null,
    end_date: string | null
  ) {
    // Fill in the dates.
    if (start_date) {
      cy.findByLabelText("Start Date")
        .focus()
        .type(`{selectAll}{backspace}${dateToMMddyyyy(start_date)}{enter}`);
      cy.findByLabelText("Start Date").focus().should("have.focus");
    }

    if (end_date) {
      cy.findByLabelText("End Date")
        .focus()
        .type(`{selectAll}{backspace}${dateToMMddyyyy(end_date)}{enter}`);
      cy.findByLabelText("End Date").should("have.focus");
    }

    if (amount) {
      cy.get("input[type=text][id$=adjustmentAmountMoney]").type(
        `{selectAll}{backspace}${amount}`
      );
    }
    clickBottomWidgetButton();
  }

  private validatePayeeAdjustmentAdded(type: string, amount: number) {
    // Check the reduction has been added.
    cy.contains("table", "Payee Adjustments").within(() => {
      cy.findByText(type).should("contain.text", type);
      cy.findByText(`-${numToPaymentFormat(amount)}`).should(
        "contain.text",
        `-${numToPaymentFormat(amount)}`
      );
    });
  }
}

export class ClaimantPage {
  static visit(ssn: string): ClaimantPage {
    ssn = ssn.replace(/-/g, "");
    cy.get('a[aria-label="Parties"]').click({ force: true });
    waitForAjaxComplete();
    cy.findByLabelText("Identification Number")
      .click({ force: true })
      .type(ssn, { delay: 10 });
    cy.get('input[type="submit"][value="Search"]').click({ force: true });
    waitForAjaxComplete();
    fineos.clickBottomWidgetButton("OK");

    return new ClaimantPage();
  }

  /**
   * Changes the personal identification details of the claimant.
   * @param changes Object with one or more of propreties to edit.
   */
  editPersonalIdentification(
    changes: Partial<PersonalIdentificationDetails>,
    upgrade: boolean
  ): this {
    cy.get(`#personalIdentificationCardWidget`)
      .findByTitle("Edit")
      .click({ force: true });
    cy.get(`#cardEditPopupWidget_PopupWidgetWrapper`).within(() => {
      if (changes.id_number_type)
        cy.findByLabelText(`Identification number type`).select(
          changes.id_number_type
        );

      if (changes.date_of_birth)
        if (upgrade) {
          // FINEOS upgrade keeps failing when using blur on the birth date in last few runs.
          // Removing for the upgrade till we stablize these Cypress tests better.
          cy.findByLabelText(`Date of birth`)
            .focus()
            .type(`{selectAll}{backspace}${changes.date_of_birth}`);
        } else {
          cy.findByLabelText(`Date of birth`)
            .focus()
            .type(`{selectAll}{backspace}${changes.date_of_birth}`)
            .blur();
        }

      if (changes.gender) cy.findByLabelText(`Gender`).select(changes.gender);

      if (changes.marital_status)
        cy.findByLabelText(`Marital status`).select(changes.marital_status);
      cy.findByText("OK").click({ force: true });
    });
    return this;
  }

  addAddress(
    address: RequireNotNull<Address, "city" | "line_1" | "state" | "zip">
  ): this {
    cy.findByText(`+ Add address`).click({ force: true });
    waitForAjaxComplete();
    cy.get(`#addressPopupWidget_PopupWidgetWrapper`).within(() => {
      cy.findByLabelText(`Address line 1`).type(`${address.line_1}`, {
        force: true,
      });
      if (address.line_2) {
        cy.findByLabelText(`Address line 2`).type(`${address.line_2}`);
      }
      cy.findByLabelText(`City`).type(`${address.city}`);
      cy.findByLabelText(`State`).select(`${address.state}`);
      cy.findByLabelText(`Zip code`).type(`${address.zip}`);
      cy.findByTitle("OK").click({ force: true });
    });
    return this;
  }

  setPhoneNumber(
    phoneNumber: string,
    verified = true,
    phoneType: Exclude<Phone["phone_type"], null | undefined> = "Cell"
  ): this {
    const strippedPhoneNumber = phoneNumber.replace(/[^0-9]/g, "");
    if (![10, 11].includes(strippedPhoneNumber.length)) {
      throw new Error(`Invalid phone number: ${phoneNumber}`);
    }

    // Deletes existing contact, if it exists
    cy.get("div#contactDetailsFrame")
      .find("div.container.card span.header-title")
      .each((el) => {
        if (el.text() === phoneType) {
          cy.wrap(
            el.parent().parent().find("span.controls span[id$='deleteIcon']")
          ).click({ force: true });
          cy.get("input[id$='Delete_Contact_yes']").click({ force: true });
        }
      });

    cy.get("a[id^='newContactDetailsCard'][id$='addPhoneContact']").click();

    let internationalCode: string;
    let areaCode: string;
    let number: string;
    if (strippedPhoneNumber.length === 11) {
      internationalCode = strippedPhoneNumber[0];
      areaCode = strippedPhoneNumber.slice(1, 4);
      number = strippedPhoneNumber.slice(4);
    } else {
      internationalCode = "1";
      areaCode = strippedPhoneNumber.slice(0, 3);
      number = strippedPhoneNumber.slice(3);
    }

    cy.get("div#addPhonePopupWidget_PopupWidgetWrapper").within(() => {
      cy.get("select[id$='contactMethod']").select(phoneType);

      cy.get("input[id$='intCode']").clear().type(internationalCode);
      cy.get("input[id$='areaCode']").clear().type(areaCode);
      cy.get("input[id$='telephoneNumber']").clear().type(number);

      cy.contains(
        "span[id$='Label']",
        verified ? "Verified" : "Unverified"
      ).click();

      cy.get("input[id$='okButtonBean']").click();
    });

    return this;
  }

  /**
   * Submits the current part of the claim intake.
   * @param timeout
   */
  private clickNext = (timeout?: number) =>
    cy
      .get('#navButtons input[value="Next "]', { timeout })
      .first()
      .click({ force: true });

  /**
   * Goes throught the claim intake process for a given claim.
   * Currently some of the options during the intake process are hard coded, since there are too many options to reasonably account for at this stage.
   * If you need more fine-grained control, use `ClaimantPage.startCreateNotification()`
   * @param claim Generated claim
   * @returns Fineos Absence Case number wrapped into `Cypress.Chainable` type.
   * @example
   * ClaimantPage.visit(claimantSSN)
   *  .createNotification(claim)
   *  .then(fineos_absence_id=>{
   *    //Further actions here...
   *  })
   */
  createNotification(
    claim: ValidClaim,
    withholdingPreference?: boolean
  ): Cypress.Chainable<string> {
    if (!claim.leave_details.reason) throw new Error(`Missing leave reason.`);
    const reason = claim.leave_details.reason as NonNullable<LeaveReason>;
    // Start the process
    return this.startCreateNotification((occupationDetails) => {
      // "Occupation Details" step.
      if (claim.hours_worked_per_week)
        occupationDetails.enterHoursWorkedPerWeek(claim.hours_worked_per_week);
      return occupationDetails.nextStep((notificationOptions) => {
        // Choose Request Type
        const reasonToRequestTypeMap: Record<
          NonNullable<LeaveReason>,
          TypeOfRequestOptions
        > = {
          "Care for a Family Member": "Caring for a family member",
          "Child Bonding":
            "Bonding with a new child (adoption/ foster care/ newborn)",
          "Military Caregiver": "Out of work for another reason",
          "Military Exigency Family": "Out of work for another reason",
          "Pregnancy/Maternity":
            "Pregnancy, birth or related medical treatment",
          "Serious Health Condition - Employee":
            "Sickness, treatment required for a medical condition or any other medical procedure",
        };
        return notificationOptions
          .chooseTypeOfRequest(reasonToRequestTypeMap[reason])
          .nextStep((reasonOfAbsence) => {
            // Fill reason of absence depending on claim contents.
            switch (reason) {
              case "Care for a Family Member":
                reasonOfAbsence.fillAbsenceReason({
                  qualifier_1: "Serious Health Condition",
                });
                reasonOfAbsence.fillAbsenceRelationship({
                  relationship_to_employee: "Sibling - Brother/Sister",
                  qualifier_1: "Biological",
                });
                break;
              case "Child Bonding":
                if (claim.leave_details.reason_qualifier)
                  reasonOfAbsence.fillAbsenceReason({
                    qualifier_1: claim.leave_details.reason_qualifier,
                  });
                break;
              case "Serious Health Condition - Employee":
                reasonOfAbsence.fillAbsenceReason({
                  relates_to: "Employee",
                  reason: "Serious Health Condition - Employee",
                  qualifier_1: "Not Work Related",
                  qualifier_2: "Sickness",
                });
                break;
              case "Pregnancy/Maternity":
                reasonOfAbsence.fillAbsenceReason({
                  relates_to: "Employee",
                  reason: "Pregnancy/Maternity",
                  qualifier_1: "Prenatal Care",
                });
                break;
              case "Military Caregiver":
                reasonOfAbsence.fillAbsenceReason({
                  relates_to: "Family",
                  reason: "Military Caregiver",
                });
                break;
              case "Military Exigency Family":
                reasonOfAbsence.fillAbsenceReason({
                  relates_to: "Family",
                  reason: "Military Exigency Family",
                  qualifier_1: "Other Additional Activities",
                });
                break;
              default:
                throw new Error(`Invalid leave reason.`);
            }
            return reasonOfAbsence.nextStep((datesOfAbsence) => {
              assertValidClaim(claim);
              // Add all available leave periods.
              const [startDate, endDate] = getLeavePeriod(claim.leave_details);
              const leavePeriodType = extractLeavePeriodType(
                claim.leave_details
              );
              datesOfAbsence.toggleLeaveScheduleSlider(leavePeriodType);
              if (claim.has_continuous_leave_periods)
                datesOfAbsence.addFixedTimeOffPeriod({
                  status: "Known",
                  start: startDate,
                  end: endDate,
                });
              if (
                claim.has_reduced_schedule_leave_periods &&
                claim.leave_details.reduced_schedule_leave_periods
              )
                datesOfAbsence.addReducedSchedulePeriod(
                  "Known",
                  claim.leave_details.reduced_schedule_leave_periods[0]
                );
              return datesOfAbsence.nextStep((absenceDetails) => {
                if (!claim?.work_pattern?.work_pattern_type)
                  throw new Error(`Missing work pattern`);
                absenceDetails
                  .selectWorkPatternType(
                    claim.work_pattern.work_pattern_type === "Rotating"
                      ? "2 weeks Rotating"
                      : claim.work_pattern.work_pattern_type
                  )
                  .applyStandardWorkWeek();
                return absenceDetails.nextStep((wrapUp) => {
                  // tax withholdings
                  fineos.waitForAjaxComplete();
                  if (withholdingPreference) {
                    cy.get(
                      "input[type='checkbox'][name$='_somSITFITOptIn_CHECKBOX']"
                    ).click();
                  }
                  // must be selected to proceed
                  cy.get(
                    "input[type='checkbox'][name$='_somSITFITVerification_CHECKBOX']"
                  ).click();

                  fineos.waitForAjaxComplete();

                  // Fill military Caregiver description if needed.
                  if (reason === "Military Caregiver")
                    absenceDetails.addMilitaryCaregiverDescription();
                  // Skip additional details step if needed
                  if (
                    reason === "Care for a Family Member" ||
                    reason === "Military Exigency Family" ||
                    reason === "Serious Health Condition - Employee" ||
                    reason === "Military Caregiver" ||
                    reason === "Child Bonding"
                  )
                    wrapUp.clickNext(20000);

                  return wrapUp.finishNotificationCreation();
                });
              });
            });
          });
      });
    });
  }

  /**
   * Starts the Fineos intake process and executes the given callback once navigated to first meaningful step of the intake.
   * @param cb
   * @returns the return value of `cb`
   */
  startCreateNotification<T>(cb: (step: OccupationDetails) => T): T {
    // Start the process
    cy.contains("span", "Create Notification").click({ force: true });
    // "Notification details" step, we are not changing anything here, so we just skip it.
    this.clickNext();
    return cb(new OccupationDetails());
  }

  paymentPreferences(): PaymentPreferencePage {
    onTab("Payment Preferences");
    waitForAjaxComplete();
    return new PaymentPreferencePage();
  }

  addCase(hasAccess: boolean): this {
    if (hasAccess) {
      cy.get(
        `div[id^="MENUBAR.PartySubjectMenu_"][id$="_MENUBAR.PartySubjectMenu"] div[title="Add Case"]`
      ).should("be.visible");
    } else {
      cy.get(
        `div[id^="MENUBAR.PartySubjectMenu_"][id$="_MENUBAR.PartySubjectMenu"] div[title="Add Case"]`
      ).should("not.be.visible");
    }
    return this;
  }
}

/**Contains utilities used within multiple pages throughout the intake process */
abstract class CreateNotificationStep {
  /**
   * Submits the current part of the claim intake.
   * @param timeout
   */
  clickNext(timeout?: number) {
    cy.get('#navButtons input[value="Next "]', { timeout })
      .first()
      .click({ force: true });
  }

  /**
   * Safely selects an option for a <select> tag with a given label
   * @param label
   * @param option
   */
  protected chooseSelectOption(label: string, option: string) {
    cy.findByLabelText(label)
      .should((el: JQuery<HTMLElement>) => {
        // Make sure the select has children and is loaded
        expect(el.children().length > 1 || el.children().first().text() !== "")
          .to.be.true;
      })
      .select(option);
    // Wait for ajax
    waitForAjaxComplete();
  }
}

class OccupationDetails extends CreateNotificationStep {
  enterHoursWorkedPerWeek(hoursWorkedPerWeek: number) {
    cy.findByLabelText("Hours worked per week").type(
      `{selectall}{backspace}${hoursWorkedPerWeek}`,
      { force: true }
    );
  }

  /**
   * Submits Occupation Details step and navigates to Notification Options step
   * @param cb
   * @returns the return value of `cb`
   */
  nextStep<T>(cb: (step: NotificationOptions) => T): T {
    this.clickNext();
    return cb(new NotificationOptions());
  }

  employmentStatus(status: string) {
    cy.findByLabelText("Employment status").select(`${status}`);
  }

  enterDateJobEnded(dateJobEnded: string) {
    cy.findByLabelText("Date job ended").type(
      `${dateToMMddyyyy(dateJobEnded)}{enter}`
    );
  }
}

type TypeOfRequestOptions =
  | "Accident or treatment required for an injury"
  | "Sickness, treatment required for a medical condition or any other medical procedure"
  | "Pregnancy, birth or related medical treatment"
  | "Bonding with a new child (adoption/ foster care/ newborn)"
  | "Caring for a family member"
  | "Out of work for another reason";

class NotificationOptions extends CreateNotificationStep {
  chooseTypeOfRequest(type: TypeOfRequestOptions): this {
    cy.contains("div", type).prev().find("input").click({ force: true });
    waitForAjaxComplete();
    cy.findByText("Request a Leave").should("be.visible");
    return this;
  }

  /**
   * Submits Notification Options step and navigates Reason Of Absence to step
   * @param cb
   * @returns the return value of `cb`
   */
  nextStep<T>(cb: (step: ReasonOfAbsence) => T): T {
    this.clickNext();
    return cb(new ReasonOfAbsence());
  }
}

/**
 * Maps to select inputs available to describe Absence Reason
 * Add new options to discriminated unions as needed
 */
export type AbsenceReasonDescription = {
  relates_to?: "Employee" | "Family";
  reason?:
    | "Serious Health Condition - Employee"
    | "Care for a Family Member"
    | "Pregnancy/Maternity"
    | "Child Bonding"
    | "Military Exigency Family"
    | "Military Caregiver";
  qualifier_1?:
    | "Not Work Related"
    | "Serious Health Condition"
    | "Birth Disability"
    | "Foster Care"
    | "Other Additional Activities"
    | "Newborn"
    | "Adoption"
    | "Prenatal Care";
  qualifier_2?: "Sickness";
  typeOfRequest?: TypeOfRequestOptions;
};
/**
 * Maps to select inputs available to describe Primary Relationship
 * Add new options to discriminated unions as needed
 */
export type PrimaryRelationshipDescription = {
  relationship_to_employee?: "Sibling - Brother/Sister" | "Child";
  qualifier_1?: "Biological";
  // @todo - currently unused, uncomment when you need to set
  // this field
  // qualifier_2?: "Equivalent Family Member" | "Opposite Sex" | "Same Sex";
};

class ReasonOfAbsence extends CreateNotificationStep {
  /**
   * Fills out the absence reason select fields with given data
   * @param desc
   */
  fillAbsenceReason(desc: AbsenceReasonDescription): this {
    if (desc.relates_to)
      this.chooseSelectOption("Absence relates to", desc.relates_to);
    if (desc.reason) this.chooseSelectOption("Absence reason", desc.reason);
    if (desc.qualifier_1)
      this.chooseSelectOption("Qualifier 1", desc.qualifier_1);
    if (desc.qualifier_2)
      this.chooseSelectOption("Qualifier 2", desc.qualifier_2);
    return this;
  }

  /**
   * Fills out the Absence Relationships select fields with given data
   * @param relationship
   */
  fillAbsenceRelationship(relationship: PrimaryRelationshipDescription): this {
    cy.get("#leaveRequestAbsenceRelationshipsWidget").within(() => {
      if (relationship.relationship_to_employee)
        this.chooseSelectOption(
          "Primary Relationship to Employee",
          relationship.relationship_to_employee
        );
      if (relationship.qualifier_1)
        this.chooseSelectOption("Qualifier 1", relationship.qualifier_1);
      // @todo - currently unused, uncomment when you need to set
      // this field
      // if (relationship.qualifier_2)
      //   this.chooseSelectOption("Qualifier 2", relationship.qualifier_2);
    });
    return this;
  }

  /**
   * Submits Reason Of Absence step and navigates Dates Of Absence to step
   * @param cb
   * @returns the return value of `cb`
   */
  nextStep<T>(cb: (step: DatesOfAbsence) => T): T {
    this.clickNext(5000);
    return cb(new DatesOfAbsence());
  }
}

type AbsenceStatus = "Known" | "Estimated" | "Please select";

type ContinuousLeavePeriod = {
  status: AbsenceStatus;
  /**MM/DD/YYYY */
  start: string;
  /**MM/DD/YYYY */
  end: string;
  /**MM/DD/YYYY */
  last_day_worked?: string;
  /**MM/DD/YYYY */
  return_to_work_date?: string;
};

class DatesOfAbsence extends CreateNotificationStep {
  /**
   * Toggles the control needed to render the Leave Period inputs according to `type`.
   * The control needs to be toggled before attempting to enter the leave period dates, but doesn't need to be toggled more than once.
   * @param type
   */
  toggleLeaveScheduleSlider(
    type: NonNullable<AbsencePeriodResponse["period_type"]>
  ): this {
    const scheduleSliderMap: Record<typeof type, string> = {
      Continuous: "One or more fixed time off periods",
      Intermittent: "Episodic / leave as needed",
      "Reduced Schedule": "Reduced work schedule",
    };
    cy.contains("div.toggle-guidance-row", scheduleSliderMap[type])
      .find("span.slider")
      .click();
    return this;
  }

  addIntermittentLeavePeriod(start: string, end: string): this {
    // Since the widget also gets re-rendered from time to time, we need to re-query it frequently.
    const withinWidget = (cb: () => unknown) =>
      cy.get(`#captureEpisodicLeaveDetailsWidget`).within(cb);
    withinWidget(() => {
      cy.findByTitle("Add a new episodic absence period").click();
      waitForAjaxComplete();
    });
    withinWidget(() => {
      cy.findByLabelText("Valid from").type(`${dateToMMddyyyy(start)}{enter}`);
      waitForAjaxComplete();
    });
    withinWidget(() => {
      cy.findByLabelText("Valid to").type(`${dateToMMddyyyy(end)}{enter}`);
      waitForAjaxComplete();
    });
    return this;
  }

  addFixedTimeOffPeriod(period: ContinuousLeavePeriod): this {
    // Since the widget also gets re-rendered from time to time, we need to re-query it frequently.
    const withinWidget = (cb: () => unknown) =>
      cy.get(`#timeOffAbsencePeriodDetailsQuickAddWidget`).within(cb);

    // Enter absence status
    withinWidget(() => {
      cy.findByLabelText("Absence status").select(period.status);
      waitForAjaxComplete();
    });

    // Enter leave start and end dates
    withinWidget(() => {
      cy.findByLabelText("Absence start date").type(
        `${dateToMMddyyyy(period.start)}{enter}`
      );
      waitForAjaxComplete();
    });

    withinWidget(() => {
      cy.findByLabelText("Absence end date").type(
        `${dateToMMddyyyy(period.end)}{enter}`
      );
      waitForAjaxComplete();
    });

    // Enter work related dates if specified
    withinWidget(() => {
      if (period.last_day_worked)
        cy.findByLabelText("Last day worked ").type(
          `${dateToMMddyyyy(period.last_day_worked)}{enter}`
        );
    });
    waitForAjaxComplete();

    withinWidget(() => {
      if (period.return_to_work_date)
        cy.findByLabelText("Return to work date").type(
          `${dateToMMddyyyy(period.return_to_work_date)}{enter}`
        );
      waitForAjaxComplete();
    });

    // Add the period
    withinWidget(() => {
      cy.findByTitle(`Quick Add`).click();
      waitForAjaxComplete();
    });
    return this;
  }

  private enterReducedWorkHours(
    leave_details: ReducedScheduleLeavePeriods
  ): void {
    const hrs = (minutes: number | null | undefined) => {
      return minutes ? Math.round(minutes / 60) : 0;
    };
    const weekdayInfo = [
      { hours: hrs(leave_details.sunday_off_minutes) },
      { hours: hrs(leave_details.monday_off_minutes) },
      { hours: hrs(leave_details.tuesday_off_minutes) },
      { hours: hrs(leave_details.wednesday_off_minutes) },
      { hours: hrs(leave_details.thursday_off_minutes) },
      { hours: hrs(leave_details.friday_off_minutes) },
      { hours: hrs(leave_details.saturday_off_minutes) },
    ];

    cy.get("input[name*='_hours']").each((input, index) => {
      cy.wrap(input).type(weekdayInfo[index].hours.toString());
    });
  }

  addReducedSchedulePeriod(
    absenceStatus: AbsenceStatus,
    reducedLeavePeriod: ReducedScheduleLeavePeriods
  ): this {
    const withinWidget = (cb: () => unknown) =>
      cy.get(`#reducedScheduleAbsencePeriodDetailsQuickAddWidget`).within(cb);

    withinWidget(() => {
      // Enter absence status
      this.chooseSelectOption("Absence status", absenceStatus);
      waitForAjaxComplete();

      if (reducedLeavePeriod.start_date)
        // Enter reduced schedule period start/end dates
        cy.findByLabelText("Absence start date")
          .type(`${dateToMMddyyyy(reducedLeavePeriod.start_date)}{enter}`)
          .then(waitForAjaxComplete);
    });
    // After this the entire widget re-renders and we need to re-query for it.
    withinWidget(() => {
      if (reducedLeavePeriod.end_date)
        cy.findByLabelText("Absence end date")
          .type(`${dateToMMddyyyy(reducedLeavePeriod.end_date)}{enter}`)
          .then(waitForAjaxComplete);
    });
    withinWidget(() => {
      // Enter hours for each weekday
      this.enterReducedWorkHours(reducedLeavePeriod);
      waitForAjaxComplete();
    });
    withinWidget(() => {
      // Submit period
      cy.findByTitle(`Quick Add`).click();
      waitForAjaxComplete();
    });

    return this;
  }

  nextStep<T>(cb: (step: WorkAbsenceDetails) => T): T {
    this.clickNext(5000);
    return cb(new WorkAbsenceDetails());
  }
}

class WorkAbsenceDetails extends CreateNotificationStep {
  selectWorkPatternType(
    type:
      | "Unknown"
      | "Fixed"
      | "2 weeks Rotating"
      | "3 weeks Rotating"
      | "4 weeks Rotating"
      | "Variable"
  ): this {
    this.chooseSelectOption("Work Pattern Type", type);
    wait();
    return this;
  }

  applyStandardWorkWeek(): this {
    cy.findByLabelText("Standard Work Week").click();
    wait();
    cy.get('input[value="Apply to Calendar"]').click({ force: true });
    return this;
  }

  addMilitaryCaregiverDescription(): this {
    cy.findByLabelText("Military Caregiver Description").type(
      "I am a parent military caregiver."
    );
    return this;
  }

  nextStep<T>(cb: (step: WrapUp) => T): T {
    this.clickNext(20000);
    return cb(new WrapUp());
  }
}

class WrapUp extends CreateNotificationStep {
  /**Looks for the Leave Case number in the Wrap Up step and returns it wrapped by Cypress. */
  private getLeaveCaseNumber() {
    const caseNumberMatcher = /NTN-[0-9]{1,6}-[A-Z]{3}-[0-9]{2}/g;
    return cy
      .findByText(/Absence Case - NTN-[0-9]{1,6}-[A-Z]{3}-[0-9]{2}/g)
      .then((el) => {
        const match = el.text().match(caseNumberMatcher);
        if (!match)
          throw new Error(
            `Couldn't find the Case Number on intake Wrap Up page.`
          );
        return cy.wrap(match[0]);
      });
  }

  /**Captures the Leave Case id number and exits the notification creation process */
  finishNotificationCreation(): Cypress.Chainable<string> {
    return this.getLeaveCaseNumber().then((absenceId) => {
      this.clickNext(20000);
      cy.contains(absenceId);
      return cy.wrap(absenceId);
    });
  }

  selectWithholdingPreference(withholdingPreference?: boolean) {
    if (withholdingPreference) {
      cy.get(
        "input[type='checkbox'][name$='_somSITFITOptIn_CHECKBOX']"
      ).click();
    }
    cy.get(
      "input[type='checkbox'][name$='_somSITFITVerification_CHECKBOX']"
    ).click();
    return this;
  }
}

type EpisodicLeavePeriodDescription = {
  startDate: string;
  endDate: string;
  timeSpanHoursStart: string;
  timeSpanHoursEnd: string;
  upgrade: boolean;
};

class RecordActualTime {
  fillTimePeriod({
    startDate,
    endDate,
    timeSpanHoursStart,
    timeSpanHoursEnd,
    upgrade,
  }: EpisodicLeavePeriodDescription) {
    // Select the episodic leave period.
    cy.findByTitle("Episodic").click();
    // Open the modal.
    cy.findByText("Record Actual").click();
    waitForAjaxComplete();
    cy.get(".popup-container").within(() => {
      // Wait for focus to be captured on the "Last Day Worked" field. This happens automatically, and only occurs
      // when the popup is ready for interaction. Annoyingly, it gets captured 2x on render, forcing us to wait as well.
      if (upgrade) {
        const startDateFormatted = format(parseISO(startDate), "MM/dd/yyyy");
        const endDateFormatted = format(parseISO(endDate), "MM/dd/yyyy");
        // Start date
        cy.findByLabelText("Absence start date")
          .focus()
          .type(`{selectall}{backspace}${startDateFormatted}`)
          .blur();
        // After entering the date and losing focus, the form re-renders and captures focus again
        // Wait for the form to capture focus
        waitForAjaxComplete();
        cy.findByLabelText("Absence start date").should("have.focus");

        // End date, same thing about focus
        cy.findByLabelText("Absence end date")
          .focus()
          .type(`{selectall}{backspace}${endDateFormatted}`)
          .blur();
        waitForAjaxComplete();
        cy.findByLabelText("Absence end date").should("have.focus");
        cy.get(
          `input[id^="timeOffAbsencePeriodDetailsWidget"][id$="timeSpanHoursStartDate"]`
        ).type(`{selectall}{backspace}${timeSpanHoursStart}`);
        cy.get(
          `input[id^="timeOffAbsencePeriodDetailsWidget"][id$="timeSpanHoursEndDate"]`
        ).type(`{selectall}{backspace}${timeSpanHoursEnd}`);
        // Submit the actual period
        cy.findByText("OK").click();
      } else {
        cy.findByLabelText("Last day worked").should("have.focus");
        const startDateFormatted = format(parseISO(startDate), "MM/dd/yyyy");
        const endDateFormatted = format(parseISO(endDate), "MM/dd/yyyy");
        // Start date
        cy.findByLabelText("Absence start date")
          .focus()
          .type(`{selectall}{backspace}${startDateFormatted}`)
          .blur();
        // After entering the date and losing focus, the form re-renders and captures focus again
        // Wait for the form to capture focus
        waitForAjaxComplete();
        cy.findByLabelText("Absence start date").should("have.focus");

        // End date, same thing about focus
        cy.findByLabelText("Absence end date")
          .focus()
          .type(`{selectall}{backspace}${endDateFormatted}`)
          .blur();
        waitForAjaxComplete();
        cy.findByLabelText("Absence end date").should("have.focus");

        cy.get(
          `input[id^="timeOffAbsencePeriodDetailsWidget"][id$="timeSpanHoursStartDate"]`
        ).type(`{selectall}{backspace}${timeSpanHoursStart}`);
        cy.get(
          `input[id^="timeOffAbsencePeriodDetailsWidget"][id$="timeSpanHoursEndDate"]`
        ).type(`{selectall}{backspace}${timeSpanHoursEnd}`);
        // Submit the actual period
        cy.findByText("OK").click();
      }
    });
    return this;
  }

  nextStep<T>(cb: (step: AdditionalReporting) => T): T {
    clickNext();
    waitForAjaxComplete();
    return cb(new AdditionalReporting());
  }
}

type AdditionalDetails = {
  reported_by?: "Employee" | "Employee Manager" | "Employer Representative";
  received_via?:
    | "Unknown"
    | "Phone"
    | "E-Mail"
    | "Paper"
    | "Fax"
    | "Mail/Post"
    | "Self Service";
  reported_date?: string;
  accepted?: "Yes" | "No" | "Unknown";
  additional_notes?: string;
  reporting_party?: string;
  upgrade: boolean;
};

export class AdditionalReporting {
  reportAdditionalDetails(details: AdditionalDetails): this {
    // Select the period
    if (details.upgrade) {
      cy.contains("td", "Incapacity").click({ force: true });
      if (details.reported_by) {
        cy.findByLabelText("Reported by").select(details.reported_by);
        waitForAjaxComplete();
      }
      if (details.reporting_party)
        cy.findByLabelText("Reporting Party Name").type(
          details.reporting_party
        );
      if (details.received_via)
        cy.findByLabelText("Received via").select(details.received_via);
      if (details.accepted)
        cy.findByLabelText("Manager accepted").select(details.accepted);
      if (details.reporting_party)
        cy.findByLabelText("Additional notes").type(details.reporting_party);
    } else {
      cy.contains("td", "Time off period").click({ force: true });
      if (details.reported_by) {
        cy.findByLabelText("Reported By").select(details.reported_by);
        waitForAjaxComplete();
      }
      if (details.reporting_party)
        cy.findByLabelText("Reporting Party Name").type(
          details.reporting_party
        );
      if (details.received_via)
        cy.findByLabelText("Received Via").select(details.received_via);
      if (details.accepted)
        cy.findByLabelText("Manager Accepted").select(details.accepted);
      if (details.reporting_party)
        cy.findByLabelText("Additional Notes").type(details.reporting_party);
    }
    cy.get("input[id*='applyActualTime']").click();
    waitForAjaxComplete();
    return this;
  }

  /**Returns back to the Claim page. */
  finishRecordingActualLeave(): void {
    clickNext();
    waitForAjaxComplete();
  }
}

class LeaveDetailsPage {
  /**
   * Function will redirect us to the claim adjudiction page
   */
  editLeavePostApproval(): AdjudicationPage {
    cy.get('input[type="submit"][value="Review"]').click();
    waitForAjaxComplete();
    cy.get('input[type="submit"][value="Edit"]').click();
    return new AdjudicationPage();
  }

  rejectSelectPlan(): AdjudicationPage {
    cy.get("tr.ListRow2.planUndecided").click();
    waitForAjaxComplete();
    cy.get('input[type="submit"][value="Reject"]').click();
    return new AdjudicationPage();
  }

  inReview(upgrade: boolean): AdjudicationPage {
    if (upgrade) {
      cy.contains("button", "Review").click({ force: true });
      cy.wait("@reactRender");
      cy.get(`.ant-modal`)
        .should("be.visible")
        .within(() => {
          cy.get('input[id="secondOption"][type="radio"]').click();
          cy.contains("button", "OK").click();
        });
      waitForAjaxComplete();
      cy.contains(
        'span[id$="_openReviewDocumentLabel"]',
        "The leave request is now in review"
      );
      waitForAjaxComplete();
      cy.wait(500);
    } else {
      cy.get('input[type="submit"][value="Review"]').click();
    }
    return new AdjudicationPage();
  }

  editLeave(): AdjudicationPage {
    cy.get('input[type="submit"][value="Edit"]').click();
    return new AdjudicationPage();
  }
}

type NoteTypes = "Leave Request Review";

class NotesPage {
  /** Adds a note of a given type and asserts it has been added succesfully. */
  addNote(type: NoteTypes, text: string) {
    cy.get("#widgetListMenu").findByText("Create New").click({ force: true });
    const selector = "#widgetListMenu .right-side-drop li:nth-child(2)";
    cy.get(selector)
      .findByText("Leave Request Review", {
        selector: "span",
      })
      .click();
    waitForAjaxComplete();
    cy.get(`#CaseNotesPopupWidgetAdd_PopupWidgetWrapper`)
      .should("be.visible")
      .within(() => {
        // @todo check if other review types have different labels
        cy.findByLabelText("Review note").type(text);
        cy.findByText("OK").click();
        waitForAjaxComplete();
      });
    this.assertHasNote(type, text);
  }

  assertHasNote(type: NoteTypes, text: string) {
    cy.get(`#CaseNotesWidgetList`)
      .contains("div.WidgetListWidget", type)
      .should("contain.text", text);
  }
}

class RestrictionsPage {
  assertRestrictionDecision(decision: "Passed") {
    cy.contains(
      "#planRestrictionsAbsencePatternsListviewWidget",
      "Supported Absence Patterns"
    ).should("contain.text", decision);
  }
}

type FixedAbsenceDateDescirtion = {
  date: string;
  all_day?: true;
  hours?: string;
  minutes?: string;
};
export type FixedTimeOffPeriodDescription = {
  start: FixedAbsenceDateDescirtion;
  end: FixedAbsenceDateDescirtion;
};

class HistoricalAbsence {
  /**To be called from Absence Hub */
  static create(upgrade?: boolean): HistoricalAbsence {
    const historicalPeriodDescription: AbsenceReasonDescription = {
      reason: "Serious Health Condition - Employee",
      relates_to: "Employee",
      qualifier_1: "Not Work Related",
      qualifier_2: "Sickness",
    };
    cy.contains("Options").click({ force: true });
    cy.contains("Add Historical Absence").click({ force: true });
    HistoricalAbsence.fillAbsenceDescription(historicalPeriodDescription);
    cy.contains("div", "timeOffHistoricalAbsencePeriodsListviewWidget")
      .find("input")
      .click();
    const mostRecentSunday = startOfWeek(new Date());
    const startDate = subDays(mostRecentSunday, 13);
    const startDateFormatted = format(startDate, "MM/dd/yyyy");
    const endDateFormatted = format(addDays(startDate, 4), "MM/dd/yyyy");

    HistoricalAbsence.fillHistoricalPeriod({
      start: { date: startDateFormatted, all_day: true },
      end: { date: endDateFormatted, all_day: true },
    });
    // Select Leave Plan
    cy.contains("div", "historicalAbsenceSelectedLeavePlansListViewWidget")
      .find("input")
      .click();
    wait();
    cy.get(
      "input[name='historicalCasePlanSelectionListviewWidget_un0_Checkbox_RowId_0_CHECKBOX']"
    ).click();
    clickBottomWidgetButton();
    clickBottomWidgetButton();
    // Click on Claimaints name to view their cases
    cy.get(
      'a[id="com.fineos.frontoffice.casemanager.casekeyinformation.CaseKeyInfoBar_un8_KeyInfoBarLink_0"]'
    ).click();
    onTab("Cases");
    const selector = upgrade
      ? ".ant-table-row-selected > td"
      : ".ListRowSelected > td";
    cy.get(selector).should(($td) => {
      expect($td.eq(upgrade ? 2 : 4)).to.contain("Absence Historical Case");
    });
    waitForAjaxComplete();
    return new HistoricalAbsence();
  }

  private static fillAbsenceDescription(
    absenceDescription: AbsenceReasonDescription
  ): void {
    if (absenceDescription.relates_to) {
      cy.findByLabelText("Absence relates to").select("Employee");
      waitForAjaxComplete();
    }
    if (absenceDescription.reason) {
      cy.findByLabelText("Absence Reason").select(
        "Serious Health Condition - Employee"
      );
      waitForAjaxComplete();
    }
    if (absenceDescription.qualifier_1) {
      cy.findByLabelText("Qualifier 1").select("Not Work Related");
      waitForAjaxComplete();
    }
    if (absenceDescription.qualifier_2) {
      cy.findByLabelText("Qualifier 2").select("Sickness");
      waitForAjaxComplete();
    }
  }

  private static fillHistoricalPeriod({
    start,
    end,
  }: Partial<FixedTimeOffPeriodDescription>): void {
    cy.findByLabelText("Start Date").should("have.focus").blur();
    waitForAjaxComplete();

    const fillSingleDate = (
      { date, all_day, hours, minutes }: FixedAbsenceDateDescirtion,
      dateType: "start" | "end"
    ) => {
      cy.findByLabelText(`${dateType === "start" ? "Start" : "End"} Date`).type(
        `{selectall}{backspace}${date}{enter}`
      );
      waitForAjaxComplete();
      if (all_day) {
        cy.get(
          `span[id^="historicalTimeOffAbsencePeriodDetailsWidget"][id$="${dateType}DateAllDay_WRAPPER"]`
        ).click();
        waitForAjaxComplete();
      } else {
        if (hours)
          cy.get(
            `input[id^="historicalTimeOffAbsencePeriodDetailsWidget"][id$="_timeSpanHours${
              dateType === "start" ? "Start" : "End"
            }Date"]`
          ).type(hours);
        waitForAjaxComplete();
        if (minutes)
          cy.get(
            `input[id^="historicalTimeOffAbsencePeriodDetailsWidget"][id$="_timeSpanMinutes${
              dateType === "start" ? "Start" : "End"
            }Date"]`
          ).type(minutes);
        waitForAjaxComplete();
      }
    };
    if (start) fillSingleDate(start, "start");
    if (end) fillSingleDate(end, "end");
    cy.get(`input[id$="_okButtonBean"]`).click();
    waitForAjaxComplete();
  }

  checkAvailability(availableBalance: string) {
    fineos.onTab("Leave Details");
    cy.findByTitle("View Leave Request").click();
    fineos.onTab("Availability");
    cy.contains("table", "Plan Availability").should(
      "contain.text",
      availableBalance
    );
    fineos.clickBottomWidgetButton("Close");
    waitForAjaxComplete();
  }

  editLeaveRequestDates(dates: Partial<FixedTimeOffPeriodDescription>) {
    fineos.onTab("Leave Details");
    cy.findByTitle("Edit Leave Request").click();
    fineos.onTab("Request Information");
    waitForAjaxComplete();
    cy.findByTitle("Edit Historical Absence Period").click();
    cy.contains("table.PopupBean", "Absence Period Change").within(() =>
      cy.findByText("Yes").click()
    );
    waitForAjaxComplete();
    cy.contains("div.popup-container", "Edit Historical Absence Period").within(
      () => HistoricalAbsence.fillHistoricalPeriod(dates)
    );
    fineos.clickBottomWidgetButton("OK");
    waitForAjaxComplete();
  }

  addFixedTimePeriod(dates: Partial<FixedTimeOffPeriodDescription>) {
    fineos.onTab("Leave Details");
    cy.findByTitle("Edit Leave Request").click();
    fineos.onTab("Request Information");
    waitForAjaxComplete();
    cy.get("#timeOffHistoricalAbsencePeriodsListviewWidget")
      .findByTitle("Add Historical Absence Period")
      .click();
    cy.contains("table.PopupBean", "Absence Period Change").within(() =>
      cy.findByText("Yes").click()
    );
    waitForAjaxComplete();
    cy.contains("div.popup-container", "Add Historical Absence Period").within(
      () => HistoricalAbsence.fillHistoricalPeriod(dates)
    );
    fineos.clickBottomWidgetButton("OK");
    waitForAjaxComplete();
  }
}

class PaymentPreferencePage {
  edit(): EditPaymentPreferences {
    cy.get('input[type="submit"][value="Edit"]').click();
    return new EditPaymentPreferences();
  }
}

class EditPaymentPreferences {
  checkBulkPayee(disabled: boolean) {
    cy.get('input[type="checkbox"][id$="bulkPayee_CHECKBOX"]').then(($el) => {
      if (disabled) cy.wrap($el).click();
      else cy.wrap($el).should("have.attr", "disabled");
    });
  }
}
