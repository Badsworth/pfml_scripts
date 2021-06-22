import { OtherIncome } from "../../src/_api";
import {
  NonEmptyArray,
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
} from "../../src/util/typeUtils";
import {
  dateToMMddyyyy,
  minutesToHoursAndMinutes,
} from "../../src/util/claims";
import {
  approveClaim,
  assertHasTask,
  assertHasDocument,
  clickBottomWidgetButton,
  denyClaim,
  markEvidence,
  onTab,
  triggerNoticeRelease,
  visitClaim,
} from "./fineos";

import { DocumentUploadRequest } from "../../src/api";

type StatusCategory =
  | "Applicability"
  | "Eligibility"
  | "Evidence"
  | "Availability"
  | "Restriction"
  | "Protocols"
  | "PlanDecision";

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
  triggerNotice(type: string): this {
    triggerNoticeRelease(type);
    return this;
  }
  approve(): this {
    approveClaim();
    return this;
  }
  deny(reason: string): this {
    denyClaim(reason);
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
  acceptLeavePlan() {
    this.onTab("Manage Request");
    cy.wait(50);
    cy.get("input[type='submit'][value='Accept']").click();
  }
}

class EvidencePage {
  receive(...args: Parameters<typeof markEvidence>): this {
    markEvidence(...args);
    return this;
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
    cy.get("input[value='Prefill with Requested Absence Periods']").click();
    cy.get("#PopupContainer input[value='Yes']").click();
    return this;
  }
}
class TasksPage {
  assertTaskExists(name: string): this {
    assertHasTask(name);
    return this;
  }

  close(name: string): this {
    cy.contains("td", name).click();
    cy.wait("@ajaxRender");
    cy.get('input[title="Close selected task"]');
    cy.wait("@ajaxRender");
    cy.wait(150);
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
   * @param documentName
   * @param documentType
   * @returns
   */
  uploadDocument(documentName: string, documentType: string): this {
    this.startDocumentCreation(documentType);
    const docName = documentName.replace(" ", "_");
    cy.get("input[type='file']").attachFile(`./${docName}.pdf`);
    clickBottomWidgetButton();
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
        onTab(part, 200);
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
    cy.findByLabelText("Start Date").type(dateToMMddyyyy(start_date));
    cy.findByLabelText("End Date").type(dateToMMddyyyy(end_date));

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
    cy.contains("table.WidgetPanel", "Amounts Pending").within(() => {
      const [first, ...rest] = amountsPending;
      // Get and assert contents of the first row. It has a unique selector.
      cy.get("tr.ListRowSelected").should(
        "contain.text",
        this.numToPaymentFormat(first.net_payment_amount)
      );
      // Get and assert contents of the other rows if present.
      rest.forEach((payment, i) => {
        cy.get(`tr.ListRow${i + 2}`).should(
          "contain.text",
          this.numToPaymentFormat(payment.net_payment_amount)
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
    cy.contains("table.WidgetPanel", "Payments Made").within(() => {
      const [first, ...rest] = paymentsMade;
      // Get and assert contents of the the first row. It has a unique selector.
      cy.get("tr.ListRowSelected").should(
        "contain.text",
        this.numToPaymentFormat(first.net_payment_amount)
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

  private numToPaymentFormat(num: number): string {
    return `${new Intl.NumberFormat("en-US", {
      style: "decimal",
    }).format(num)}.00`;
  }
}
