import {
  BankAccountType,
  PaymentPreferenceMethod,
} from "../../src/models/PaymentPreference";
import Claim, {
  ClaimStatus,
  ContinuousLeavePeriod,
  DurationBasis,
  EmploymentStatus,
  FrequencyIntervalBasis,
  IntermittentLeavePeriod,
  PhoneType,
  ReasonQualifier,
  ReducedScheduleLeavePeriod,
  WorkPattern,
  WorkPatternDay,
  WorkPatternType,
} from "../../src/models/Claim";
import EmployerBenefit, {
  EmployerBenefitFrequency,
  EmployerBenefitType,
} from "../../src/models/EmployerBenefit";
import OtherIncome, {
  OtherIncomeFrequency,
  OtherIncomeType,
} from "../../src/models/OtherIncome";
import PreviousLeave, {
  PreviousLeaveReason,
} from "../../src/models/PreviousLeave";
import Address from "../../src/models/Address";
import EmployerClaim from "../../src/models/EmployerClaim";
import LeaveReason from "../../src/models/LeaveReason";
import { set } from "lodash";

export class BaseMockClaimBuilder {
  employed() {
    set(this.claimAttrs, "employer_fein", "12-3456789");
    set(this.claimAttrs, "leave_details.employer_notified", true);
    set(this.claimAttrs, "hours_worked_per_week", 30);
    set(
      this.claimAttrs,
      "leave_details.employer_notification_date",
      "2021-01-01"
    );
    return this;
  }

  /**
   * @returns {BaseMockClaimBuilder}
   */
  absenceId() {
    set(this.claimAttrs, "fineos_absence_id", "NTN-111-ABS-01");
    return this;
  }

  address(attrs) {
    set(
      this.claimAttrs,
      "residential_address",
      attrs
        ? new Address(attrs)
        : new Address({
            city: "Boston",
            line_1: "1234 My St.",
            line_2: null,
            state: "MA",
            zip: "00000",
          })
    );
    return this;
  }

  continuous(leavePeriodAttrs = {}) {
    set(
      this.claimAttrs,
      "leave_details.continuous_leave_periods[0]",
      new ContinuousLeavePeriod(
        Object.assign(
          {
            leave_period_id: "mock-leave-period-id",
            start_date: "2021-01-01",
            end_date: "2021-06-01",
          },
          leavePeriodAttrs
        )
      )
    );
    return this;
  }

  intermittent(leavePeriodAttrs = {}) {
    set(
      this.claimAttrs,
      "leave_details.intermittent_leave_periods[0]",
      new IntermittentLeavePeriod(
        Object.assign(
          {
            leave_period_id: "mock-leave-period-id",
            start_date: "2021-02-01",
            end_date: "2021-07-01",
            duration: 3,
            duration_basis: DurationBasis.hours,
            frequency: 6,
            frequency_interval: 6,
            frequency_interval_basis: FrequencyIntervalBasis.months,
          },
          leavePeriodAttrs
        )
      )
    );
    return this;
  }

  reducedSchedule(leavePeriodAttrs = {}) {
    set(
      this.claimAttrs,
      "leave_details.reduced_schedule_leave_periods[0]",
      new ReducedScheduleLeavePeriod(
        Object.assign(
          {
            leave_period_id: "mock-leave-period-id",
            start_date: "2021-02-01",
            end_date: "2021-07-01",
          },
          leavePeriodAttrs
        )
      )
    );
    return this;
  }

  bondingLeaveReason() {
    set(this.claimAttrs, "leave_details.reason", LeaveReason.bonding);
    return this;
  }

  medicalLeaveReason() {
    set(this.claimAttrs, "leave_details.reason", LeaveReason.medical);
    return this;
  }

  otherIncome(attrs) {
    set(
      this.claimAttrs,
      "other_incomes",
      attrs
        ? attrs.map((attr) => new OtherIncome(attr))
        : [
            new OtherIncome({
              income_amount_dollars: 125,
              income_amount_frequency: OtherIncomeFrequency.weekly,
              income_end_date: "2021-01-01",
              income_start_date: "2021-01-30",
              income_type: OtherIncomeType.otherEmployer,
            }),
          ]
    );
    set(this.claimAttrs, "has_other_incomes", true);
    set(this.claimAttrs, "other_incomes_awaiting_approval", false);
    return this;
  }

  otherIncomeFromUnemployment() {
    set(this.claimAttrs, "other_incomes", [
      new OtherIncome({
        income_amount_dollars: 125,
        income_amount_frequency: OtherIncomeFrequency.weekly,
        income_end_date: "2021-01-01",
        income_start_date: "2021-01-30",
        income_type: OtherIncomeType.unemployment,
      }),
    ]);
    set(this.claimAttrs, "has_other_incomes", true);
    set(this.claimAttrs, "other_incomes_awaiting_approval", false);
    return this;
  }

  previousLeavePregnancyFromOtherEmployer() {
    set(this.claimAttrs, "previous_leaves", [
      new PreviousLeave({
        previous_leave_id: 1,
        is_for_current_employer: false,
        leave_end_date: "2021-02-01",
        leave_reason: PreviousLeaveReason.pregnancy,
        leave_start_date: "2021-01-01",
      }),
    ]);
    return this;
  }

  previousLeaveMedicalFromCurrentEmployer() {
    set(this.claimAttrs, "previous_leaves", [
      new PreviousLeave({
        previous_leave_id: 1,
        is_for_current_employer: true,
        leave_end_date: "2021-02-01",
        leave_reason: PreviousLeaveReason.medical,
        leave_start_date: "2021-01-01",
      }),
    ]);
    return this;
  }

  employerBenefit(attrs) {
    set(
      this.claimAttrs,
      "employer_benefits",
      attrs
        ? attrs.map((attr) => new EmployerBenefit(attr))
        : [
            new EmployerBenefit({
              benefit_amount_dollars: 500,
              benefit_amount_frequency: EmployerBenefitFrequency.weekly,
              benefit_end_date: "2021-02-01",
              benefit_start_date: "2021-01-01",
              benefit_type: EmployerBenefitType.familyOrMedicalLeave,
              employer_benefit_id: 1,
            }),
          ]
    );

    if (this instanceof MockClaimBuilder) {
      // only the MockClaimBuilder has this attr, MockEmployerClaimBuilder does not
      set(this.claimAttrs, "has_employer_benefits", true);
    }

    return this;
  }
}

/**
 * @class Employer Claim
 * @example
 *  new MockEmployerClaimBuilder()
 *    .completed()
 *    .create();
 */
export class MockEmployerClaimBuilder extends BaseMockClaimBuilder {
  constructor(middleName = "") {
    super();
    this.claimAttrs = {
      employer_dba: "Work Inc.",
      employer_id: "dda903f-f093f-ff900",
      first_name: "Jane",
      middle_name: middleName,
      last_name: "Doe",
      date_of_birth: "****-07-17",
      tax_identifier: "***-**-1234",
      follow_up_date: "2020-10-10",
    };
  }

  /**
   * @returns {MockEmployerClaimBuilder}
   */
  completed(isIntermittent = false) {
    this.employed();
    this.address();
    if (isIntermittent) {
      this.intermittent();
    } else {
      this.continuous();
      this.reducedSchedule();
    }
    this.previousLeavePregnancyFromOtherEmployer();
    this.employerBenefit();
    this.absenceId();
    set(this.claimAttrs, "leave_details.reason", LeaveReason.medical);
    return this;
  }

  /**
   * @returns {MockEmployerClaimBuilder}
   */
  employer_id(employerId) {
    set(this.claimAttrs, "employer_id", employerId);
    return this;
  }

  /**
   * @returns {MockEmployerClaimBuilder}
   */
  reviewable(setting = true) {
    set(this.claimAttrs, "is_reviewable", !!setting);
    return this;
  }

  /**
   * @returns {EmployerClaim}
   */
  create() {
    return new EmployerClaim(this.claimAttrs);
  }
}

/**
 * A class that has chainable functions for conveniently creating mock claims
 * with prefilled data. Chain together multiple function calls, then call
 * the `create` function at the end to get the Claim object.
 * @class
 * @example
 *  new MockClaimBuilder()
 *    .continuous()
 *    .intermittent()
 *    .create();
 */
export class MockClaimBuilder extends BaseMockClaimBuilder {
  constructor() {
    super();
    this.claimAttrs = {
      application_id: "mock_application_id",
      status: ClaimStatus.started,
    };
  }

  /**
   * @returns {MockClaimBuilder}
   */
  id(application_id) {
    set(this.claimAttrs, "application_id", application_id);
    return this;
  }

  /**
   * @param {object} [leavePeriodAttrs]
   * @returns {MockClaimBuilder}
   */
  continuous(leavePeriodAttrs = {}) {
    set(this.claimAttrs, "has_continuous_leave_periods", true);
    super.continuous(leavePeriodAttrs);
    return this;
  }

  /**
   * Sets payment method to paper check
   * @returns {MockClaimBuilder}
   */
  check() {
    set(
      this.claimAttrs,
      "payment_preference.payment_method",
      PaymentPreferenceMethod.check
    );
    return this;
  }

  /**
   * Sets payment method to direct deposit
   * @returns {MockClaimBuilder}
   */
  directDeposit() {
    set(
      this.claimAttrs,
      "payment_preference.payment_method",
      PaymentPreferenceMethod.ach
    );
    set(this.claimAttrs, "payment_preference.account_number", "091000022");
    set(
      this.claimAttrs,
      "payment_preference.bank_account_type",
      BankAccountType.checking
    );
    set(this.claimAttrs, "payment_preference.routing_number", "1234567890");
    return this;
  }

  /**
   * @returns {MockClaimBuilder}
   */
  hasOtherId() {
    set(this.claimAttrs, "has_state_id", false);
    return this;
  }

  /**
   * @returns {MockClaimBuilder}
   */
  hasStateId() {
    set(this.claimAttrs, "has_state_id", true);
    set(this.claimAttrs, "mass_id", "*********");
    return this;
  }

  /**
   * @param {object} [leavePeriodAttrs]
   * @returns {MockClaimBuilder}
   */
  intermittent(leavePeriodAttrs = {}) {
    set(this.claimAttrs, "has_intermittent_leave_periods", true);
    super.intermittent(leavePeriodAttrs);
    return this;
  }

  /**
   * @param {object} [leavePeriodAttrs]
   * @returns {MockClaimBuilder}
   */
  reducedSchedule(leavePeriodAttrs = {}) {
    set(this.claimAttrs, "has_reduced_schedule_leave_periods", true);
    super.reducedSchedule({
      monday_off_minutes: 6.5 * 60,
      friday_off_minutes: 8 * 60,
      ...leavePeriodAttrs,
    });
    return this;
  }

  /**
   * @param {string} birthDate Child's birth date in ISO-8601 format. Defaults
   * to "2012-02-12"
   * @returns {MockClaimBuilder}
   */
  bondingBirthLeaveReason(birthDate = "2012-02-12") {
    this.bondingLeaveReason();
    set(
      this.claimAttrs,
      "leave_details.reason_qualifier",
      ReasonQualifier.newBorn
    );
    set(this.claimAttrs, "leave_details.child_birth_date", birthDate);
    return this;
  }

  /**
   * @param {string} placementDate Child's placement date in ISO-8601 format. Defaults
   * to "2020-02-14"
   * @returns {MockClaimBuilder}
   */
  bondingAdoptionLeaveReason(placementDate = "2012-02-14") {
    this.bondingLeaveReason();
    set(
      this.claimAttrs,
      "leave_details.reason_qualifier",
      ReasonQualifier.adoption
    );
    set(this.claimAttrs, "leave_details.child_placement_date", placementDate);
    return this;
  }

  /**
   * @param {string} placementDate Child's placement date in ISO-8601 format. Defaults
   * to "2020-02-14"
   * @returns {MockClaimBuilder}
   */
  bondingFosterCareLeaveReason(placementDate = "2012-02-14") {
    this.bondingLeaveReason();
    set(
      this.claimAttrs,
      "leave_details.reason_qualifier",
      ReasonQualifier.fosterCare
    );
    set(this.claimAttrs, "leave_details.child_placement_date", placementDate);
    return this;
  }

  /**
   * @returns {MockClaimBuilder}
   */
  hasFutureChild() {
    set(this.claimAttrs, "leave_details.has_future_child_date", true);
    return this;
  }

  /**
   * @returns {MockClaimBuilder}
   */
  employed() {
    set(this.claimAttrs, "employment_status", EmploymentStatus.employed);
    super.employed();
    return this;
  }

  /**
   * @returns {MockClaimBuilder}
   */
  noOtherLeave() {
    set(this.claimAttrs, "has_employer_benefits", false);
    this.noOtherIncomes();
    this.noPreviousLeave();
    return this;
  }

  noOtherIncomes() {
    set(this.claimAttrs, "has_other_incomes", false);
    set(this.claimAttrs, "other_incomes_awaiting_approval", false);
    return this;
  }

  noPreviousLeave() {
    set(this.claimAttrs, "has_previous_leaves", false);
    return this;
  }

  previousLeave(attrs) {
    set(
      this.claimAttrs,
      "previous_leaves",
      attrs
        ? attrs.map((attr) => new PreviousLeave(attr))
        : [
            new PreviousLeave({
              previous_leave_id: 1,
              is_for_current_employer: false,
              leave_end_date: "2020-02-01",
              leave_reason: PreviousLeaveReason.pregnancy,
              leave_start_date: "2020-01-01",
            }),
          ]
    );
    return this;
  }

  previousLeavePregnancyFromOtherEmployer() {
    super.previousLeavePregnancyFromOtherEmployer();
    set(this.claimAttrs, "has_previous_leaves", true);
    return this;
  }

  previousLeaveMedicalFromCurrentEmployer() {
    super.previousLeaveMedicalFromCurrentEmployer();
    set(this.claimAttrs, "has_previous_leaves", true);
    return this;
  }

  /**
   * @returns {MockClaimBuilder}
   */
  notifiedEmployer() {
    set(this.claimAttrs, "leave_details.employer_notified", true);
    set(
      this.claimAttrs,
      "leave_details.employer_notification_date",
      "2020-08-26"
    );
    return this;
  }

  /**
   * @returns {MockClaimBuilder}
   */
  notNotifiedEmployer() {
    set(this.claimAttrs, "leave_details.employer_notified", false);
    set(this.claimAttrs, "leave_details.employer_notification_date", null);
    return this;
  }

  /**
   * @returns {MockClaimBuilder}
   */
  pregnant() {
    set(this.claimAttrs, "leave_details.pregnant_or_recent_birth", true);
    return this;
  }

  /**
   * All required data is present but the claim hasn't been marked
   * as Completed yet in the API
   * @returns {MockClaimBuilder}
   */
  complete() {
    this.submitted();
    this.paymentPrefSubmitted();
    return this;
  }

  /**
   * Claim has all required data and has been marked as completed in the API
   * @returns {MockClaimBuilder}
   */
  completed() {
    this.complete();
    set(this.claimAttrs, "status", ClaimStatus.completed);

    return this;
  }

  /**
   * Part 1 steps are complete but not yet submitted to API
   * @param {object} [options]
   * @param {boolean} [options.excludeLeavePeriod]
   * @returns {MockClaimBuilder}
   */
  part1Complete(options = {}) {
    this.verifiedId();
    this.medicalLeaveReason();
    this.employed();
    this.noOtherLeave();
    this.address();
    this.workPattern({ work_pattern_type: WorkPatternType.fixed });

    if (!options.excludeLeavePeriod) this.continuous();

    return this;
  }

  /**
   * Part 1 steps are complete and submitted to API
   * @returns {MockClaimBuilder}
   */
  submitted() {
    this.part1Complete();
    this.absenceId();
    set(this.claimAttrs, "status", ClaimStatus.submitted);

    return this;
  }

  /**
   * Part 2 step is completed and submitted to API
   * @returns {MockClaimBuilder}
   */
  paymentPrefSubmitted() {
    this.submitted();
    this.directDeposit();
    set(this.claimAttrs, "has_submitted_payment_preference", true);

    return this;
  }

  /**
   * @param {object} attrs Address object
   * @returns {MockClaimBuilder}
   */
  address(attrs) {
    set(this.claimAttrs, "has_mailing_address", false);
    super.address(attrs);
    return this;
  }

  /**
   * @param {object} attrs Address object
   * @returns {MockClaimBuilder}
   */
  mailingAddress(attrs) {
    set(this.claimAttrs, "has_mailing_address", true);
    set(
      this.claimAttrs,
      "mailing_address",
      attrs
        ? new Address(attrs)
        : new Address({
            city: "Boston",
            line_1: "124 My St.",
            line_2: null,
            state: "MA",
            zip: "00000",
          })
    );
    return this;
  }

  /**
   * @returns {MockClaimBuilder}
   */
  verifiedId(middleName) {
    set(this.claimAttrs, "first_name", "Jane");
    set(this.claimAttrs, "middle_name", middleName || "");
    set(this.claimAttrs, "last_name", "Doe");
    set(this.claimAttrs, "phone", {
      phone_number: "123-456-****",
      phone_type: PhoneType.cell,
    });
    set(this.claimAttrs, "date_of_birth", "****-07-17");
    set(this.claimAttrs, "tax_identifier", "***-**-****");
    this.address();
    this.hasStateId();
    return this;
  }

  /**
   * @returns {MockClaimBuilder}
   */
  workPattern(attrs = {}) {
    set(this.claimAttrs, "work_pattern", new WorkPattern(attrs));

    return this;
  }

  /**
   * @returns {MockClaimBuilder}
   */
  fixedWorkPattern() {
    set(
      this.claimAttrs,
      "work_pattern",
      new WorkPattern({
        work_pattern_type: WorkPatternType.fixed,
        work_pattern_days: [
          new WorkPatternDay({
            day_of_week: "Sunday",
            minutes: 0,
          }),
          new WorkPatternDay({
            day_of_week: "Monday",
            minutes: 8 * 60,
          }),
          new WorkPatternDay({
            day_of_week: "Tuesday",
            minutes: 8 * 60,
          }),
          new WorkPatternDay({
            day_of_week: "Wednesday",
            minutes: 8 * 60,
          }),
          new WorkPatternDay({
            day_of_week: "Thursday",
            minutes: 8 * 60,
          }),
          new WorkPatternDay({
            day_of_week: "Friday",
            minutes: 8 * 60,
          }),
          new WorkPatternDay({
            day_of_week: "Saturday",
            minutes: 0,
          }),
        ],
      })
    );

    set(this.claimAttrs, "hours_worked_per_week", 40);

    return this;
  }

  /**
   * @returns {MockClaimBuilder}
   */
  variableWorkPattern() {
    const workPattern = WorkPattern.createWithWeek(40 * 60, {
      work_pattern_type: WorkPatternType.variable,
    });

    set(this.claimAttrs, "work_pattern", workPattern);
    set(this.claimAttrs, "hours_worked_per_week", 40);

    return this;
  }

  /**
   * @returns {Claim}
   */
  create() {
    return new Claim(this.claimAttrs);
  }
}
