import {
  Address,
  OtherIncome,
  PaymentPreferenceRequestBody,
  ReducedScheduleLeavePeriods,
} from "../../src/_api";
import {
  AllNotNull,
  FineosTasks,
  NonEmptyArray,
  PersonalIdentificationDetails,
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

import { DocumentUploadRequest } from "../../src/api";
import { fineos } from ".";
import { LeaveReason } from "../../src/generation/Claim";
import { differenceInBusinessDays, format, parseISO } from "date-fns";

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
  recordActualLeave<T>(cb: (page: RecordActualTime) => T): T {
    // Start the submission process.
    cy.findByText("Record Actual").click({ force: true });
    waitForAjaxComplete();
    return cb(new RecordActualTime());
  }
  paidLeave(cb: (page: PaidLeavePage) => unknown): this {
    cy.findByText("Absence Paid Leave Case", { selector: "a" }).click();
    cb(new PaidLeavePage());
    cy.findByText("Absence Case", { selector: "a" }).click();
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
  documents(cb: (page: DocumentsPage) => unknown): this {
    onTab("Documents");
    cb(new DocumentsPage());
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
  ): this {
    onTab("Task");
    onTab("Processes");
    cy.contains(".TreeNodeElement", type).click({
      force: true,
    });
    // When we're firing time triggers, there's always the possibility that the trigger has already happened
    // by the time we get here. When this happens, the "Properties" button will be grayed out and unclickable.
    cy.get('input[type="submit"][value="Properties"]').then((el) => {
      if (el.is(":disabled")) {
        cy.log("Skipping trigger because this time trigger has already fired");
        return;
      }
      cy.wrap(el).click();
      cy.get('input[type="submit"][value="Continue"]').click({ force: true });
      cy.contains(".TreeNodeContainer", type, {
        timeout: 20000,
      })
        .find("input[type='checkbox']")
        .should("be.checked");
    });

    return this;
  }
  approve(): this {
    // This button turns out to be unclickable without force, because selecting
    // it seems to scroll it out of view. Force works around that.
    cy.get('a[title="Approve the Pending Leaving Request"]').click({
      force: true,
    });
    waitForAjaxComplete();
    assertClaimStatus("Approved");
    return this;
  }
  deny(reason: string): this {
    cy.get("input[type='submit'][value='Adjudicate']").click();
    // Make sure the page is fully loaded by waiting for the leave plan to show up.
    cy.get("table[id*='selectedLeavePlans'] tr")
      .should("have.length", 1)
      .click();
    cy.get("input[type='submit'][value='Reject']").click();
    clickBottomWidgetButton("OK");

    cy.get('a[title="Deny the Pending Leave Request"]').click();
    cy.get('span[id="leaveRequestDenialDetailsWidget"]')
      .find("select")
      .select(reason);
    cy.get('input[type="submit"][value="OK"]').click();
    assertClaimStatus("Declined");
    return this;
  }

  // This will deny extended time in the Leave Details.
  // No assert ClaimStatus for Declined for the absence case
  // won't say "Declined".
  denyExtendedTime(reason: string): this {
    cy.get("tr.ListRowSelected").click();
    cy.get('a[title="Deny the Pending Leave Request"]').click({
      force: true,
    });
    cy.get('span[id="leaveRequestDenialDetailsWidget"]')
      .find("select")
      .select(reason);
    cy.get('input[type="submit"][value="OK"]').click();
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
  reviewClaim(): this {
    onTab("Leave Details");
    cy.contains("td", "Approved").click();
    cy.get('input[title="Review a Leave Request"').click();
    waitForAjaxComplete();
    onTab("Absence Hub");
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
  requestInformation(cb: (page: RequestInformationPage) => unknown): this {
    this.onTab("Request Information", "Request Details");
    cb(new RequestInformationPage());
    return this;
  }
  acceptLeavePlan() {
    this.onTab("Manage Request");
    cy.get("input[type='submit'][value='Accept']").click({ force: true });
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
    cy.get("input[type='text'][id$='_startDate']").click();
    cy.get("input[type='text'][id$='_startDate']").type(
      `{selectall}{backspace}${newStartDate}`
    );
    fineos.waitForAjaxComplete();
    cy.get("input[type='text'][id$='_endDate']").click();
    cy.get("input[type='text'][id$='_endDate']").type(
      `{selectall}{backspace}${newEndDate}`
    );
    fineos.waitForAjaxComplete();
    cy.get("input[title='OK']").click();
  }

  editRequestDates(newStartDate: string, newEndDate: string) {
    cy.get("input[value='Edit']").click();
    cy.get("#PopupContainer input[value='Yes']").click();
    cy.wait("@ajaxRender");
    cy.wait(200);
    this.enterNewLeaveDates(newStartDate, newEndDate);
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
    cy.wait("@ajaxRender");
    cy.wait(200);
    cy.get("input[value='Add']").click();
    cy.get(
      "#AddManagedRequirementPopupWidget_PopupWidgetWrapper input[type='submit'][value='Ok']"
    ).click();
    cy.get("#footerButtonsBar input[value='OK']").click();
  }
  complete(receipt = "Received", reason = "Complete Employer Confirmation") {
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
    cy.findByTitle(name, { exact: false }).click({ force: true });
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

  editActivityDescription(name: string, comment: string): this {
    cy.contains("td", "Approved Leave Start Date Change").click();
    cy.wait("@ajaxRender");
    cy.get('input[title="Edit this Activity"').click();
    cy.wait("@ajaxRender");
    cy.get("textarea[name*='BasicDetailsWidget1_un11_Description']").type(
      comment
    );
    cy.wait(150);
    cy.get("#footerButtonsBar input[value='OK']").click();
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

  /**
   * Goes through the document upload process and returns back to the documents page
   * @param businessType - name of the document type in fineos
   * @returns
   */
  uploadDocument(documentType: DocumentUploadRequest["document_type"]): this {
    this.startDocumentCreation(documentType);
    cy.get("input[type='file']").attachFile(
      `./${getFixtureDocumentName(documentType)}.pdf`
    );
    clickBottomWidgetButton();
    this.assertDocumentExists(documentType);
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
    cy.labelled("Business Type").type(`${documentType}{enter}`);
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
    cy.labelled(
      "Will you use any employer-sponsored accrued paid leave for a qualifying reason during this leave?"
    ).select("Yes");
    cy.labelled("Will you use accrued paid leave from this employer?").select(
      leave.is_for_current_employer ? "Yes" : "No"
    );
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

/**
 * Future or made payment.
 */
type Payment = { net_payment_amount: number };

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
    cy.findByLabelText("Start Date").should("have.focus");

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
      cy.findByText(`-${this.numToPaymentFormat(amount)}`).should(
        "contain.text",
        `-${this.numToPaymentFormat(amount)}`
      );
    });
  }

  /**
   * Asserts there are pending payments for a given amount.
   * @param amountsPending array of expected pending payments.
   * @returns
   */
  assertAmountsPending(amountsPending: Payment[]): this {
    this.onTab("Financials", "Payment History", "Amounts Pending");
    if (!amountsPending.length) return this;
    // Get the table
    cy.contains("table.WidgetPanel", "Amounts Pending")
      .find("table.ListTable")
      .within(() => {
        amountsPending.forEach((payment, i) => {
          // Note: We don't want to rely on row classes here, as they are added an indeterminate time after the page is
          // rendered.
          cy.get(`tr:nth-child(${i + 1})`).should(
            "contain.text",
            payment.net_payment_amount
          );
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
            this.numToPaymentFormat(payment.net_payment_amount)
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
          this.numToPaymentFormat(payment.net_payment_amount)
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
    cy.get('span[id="CaseDetails_un29_AssignedTo"]').should((element) => {
      expect(
        element,
        `Expected the Assigned To display the following "${assign}"`
      ).to.have.text(assign);
    });
    return this;
  }

  private numToPaymentFormat(num: number): string {
    const decimal = num % 1 ? "" : ".00";
    return `${new Intl.NumberFormat("en-US", {
      style: "decimal",
    }).format(num)}${decimal}`;
  }
}

class BenefitsExtensionPage {
  private continue(text = "Next") {
    clickBottomWidgetButton(text);
    cy.wait("@ajaxRender");
    cy.wait(150);
  }

  private enterExtensionLeaveDates(newStartDate: string, newEndDate: string) {
    cy.labelled("Absence status").select("Known");
    cy.get("input[id='timeOffAbsencePeriodDetailsWidget_un19_startDate']").type(
      `{selectall}{backspace}${newStartDate}{enter}`
    );
    cy.wait("@ajaxRender");
    cy.wait(200);
    cy.get("input[id='timeOffAbsencePeriodDetailsWidget_un19_endDate']").type(
      `{selectall}{backspace}${newEndDate}{enter}`
    );
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
  }

  extendLeave(newStartDate: string, newEndDate: string): this {
    onTab("Capture Additional Time");
    // This assumes the claim is continuos
    cy.findByTitle("Add Time Off Period").click();
    this.enterExtensionLeaveDates(newStartDate, newEndDate);
    this.continue();
    this.continue();
    this.continue();
    this.continue();
    this.continue("OK");
    return this;
  }
}

export class ClaimantPage {
  static visit(ssn: string): ClaimantPage {
    ssn = ssn.replace(/-/g, "");
    cy.get('a[aria-label="Parties"]').click();
    waitForAjaxComplete();
    cy.contains("td", "Identification Number")
      .next()
      .within(() => cy.get("input").type(ssn));
    cy.get('input[type="submit"][value="Search"]').click();
    waitForAjaxComplete();
    fineos.clickBottomWidgetButton("OK");
    waitForAjaxComplete();
    return new ClaimantPage();
  }
  /**
   * Changes the personal identification details of the claimant.
   * @param changes Object with one or more of propreties to edit.
   */
  editPersonalIdentification(
    changes: Partial<PersonalIdentificationDetails>
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
        cy.findByLabelText(`Date of birth`)
          .focus()
          .type(`{selectAll}{backspace}${changes.date_of_birth}`)
          .blur();

      if (changes.gender) cy.findByLabelText(`Gender`).select(changes.gender);

      if (changes.marital_status)
        cy.findByLabelText(`Marital status`).select(changes.marital_status);
      cy.findByText("OK").click({ force: true });
    });
    return this;
  }

  addAddress(address: AllNotNull<Address>): this {
    cy.findByText(`+ Add address`).click({ force: true });
    waitForAjaxComplete();
    cy.get(`#addressPopupWidget_PopupWidgetWrapper`).within(() => {
      cy.findByLabelText(`Address line 1`).type(`${address.line_1}`);
      cy.findByLabelText(`Address line 2`).type(`${address.line_2}`);
      cy.findByLabelText(`City`).type(`${address.city}`);
      cy.findByLabelText(`State`).select(`${address.state}`);
      cy.findByLabelText(`Zip code`).type(`${address.zip}`);
      cy.findByTitle("OK").click({ force: true });
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
  createNotification(claim: ValidClaim): Cypress.Chainable<string> {
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
              if (claim.has_continuous_leave_periods)
                // @TODO adjust leave period/status as needed
                datesOfAbsence
                  .toggleLeaveScheduleSlider("continuos")
                  .addFixedTimeOffPeriod({
                    status: "Known",
                    start: startDate,
                    end: endDate,
                  });
              if (claim.has_intermittent_leave_periods)
                datesOfAbsence
                  // @TODO add method to add intermittent leave period
                  .toggleLeaveScheduleSlider("intermittent");
              if (
                claim.has_reduced_schedule_leave_periods &&
                claim.leave_details.reduced_schedule_leave_periods
              )
                datesOfAbsence
                  .toggleLeaveScheduleSlider("reduced")
                  .addReducedSchedulePeriod(
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
    cy.contains("span", "Create Notification").click();
    // "Notification details" step, we are not changing anything here, so we just skip it.
    this.clickNext();
    return cb(new OccupationDetails());
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
    wait();
  }
}

class OccupationDetails extends CreateNotificationStep {
  enterHoursWorkedPerWeek(hoursWorkedPerWeek: number) {
    cy.findByLabelText("Hours worked per week").type(
      `{selectall}{backspace}${hoursWorkedPerWeek}`
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
    cy.contains("div", type).prev().find("input").click();
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
 * Maps to select inputs available to describe Absense Reason
 */
export type AbsenceReasonDescription = {
  relates_to?: string;
  reason?: string;
  qualifier_1?: string;
  qualifier_2?: string;
};
/**
 * Maps to select inputs available to describe Primary Relationship
 */
export type PrimaryRelationshipDescription = {
  relationship_to_employee?: string;
  qualifier_1?: string;
  qualifier_2?: string;
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
      if (relationship.qualifier_2)
        this.chooseSelectOption("Qualifier 2", relationship.qualifier_2);
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
    type: "continuos" | "intermittent" | "reduced"
  ): this {
    const scheduleSliderMap: Record<typeof type, string> = {
      continuos: "One or more fixed time off periods",
      intermittent: "Episodic / leave as needed",
      reduced: "Reduced work schedule",
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
}

type EpisodicLeavePeriodDescription = {
  startDate: string;
  endDate: string;
  timeSpanHoursStart: string;
  timeSpanHoursEnd: string;
};
class RecordActualTime {
  fillTimePeriod({
    startDate,
    endDate,
    timeSpanHoursStart,
    timeSpanHoursEnd,
  }: EpisodicLeavePeriodDescription) {
    // Select the episodic leave period.
    cy.findByTitle("Episodic").click();
    // Open the modal.
    cy.findByText("Record Actual").click();
    waitForAjaxComplete();
    cy.get(".popup-container").within(() => {
      // Wait for focus to be captured on the "Last Day Worked" field. This happens automatically, and only occurs
      // when the popup is ready for interaction. Annoyingly, it gets captured 2x on render, forcing us to wait as well.
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
};
export class AdditionalReporting {
  reportAdditionalDetails(details: AdditionalDetails): this {
    // Select the period
    cy.contains("td", "Time off period").click({ force: true });
    if (details.reported_by) {
      cy.findByLabelText("Reported By").select(details.reported_by);
      waitForAjaxComplete();
    }
    if (details.reporting_party)
      cy.findByLabelText("Reporting Party Name").type(details.reporting_party);
    if (details.received_via)
      cy.findByLabelText("Received Via").select(details.received_via);
    if (details.accepted)
      cy.findByLabelText("Manager Accepted").select(details.accepted);
    if (details.reporting_party)
      cy.findByLabelText("Additional Notes").type(details.reporting_party);
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
}

type NoteTypes = "Leave Request Review";
class NotesPage {
  /** Adds a note of a given type and asserts it has been added succesfully. */
  addNote(type: NoteTypes, text: string) {
    cy.findByText("Create New").click();
    cy.findByText(type, { selector: "span" }).click();
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
