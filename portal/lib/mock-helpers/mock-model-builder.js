import {
  BankAccountType,
  PaymentPreferenceMethod,
} from "../../src/models/PaymentPreference";
import BenefitsApplication, {
  BenefitsApplicationStatus,
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
} from "../../src/models/BenefitsApplication";
import EmployerBenefit, {
  EmployerBenefitType,
} from "../../src/models/EmployerBenefit";
import OtherIncome, {
  OtherIncomeFrequency,
  OtherIncomeType,
} from "../../src/models/OtherIncome";
import PreviousLeave, {
  PreviousLeaveReason,
  PreviousLeaveType,
} from "../../src/models/PreviousLeave";

import Address from "../../src/models/Address";
import ConcurrentLeave from "../../src/models/ConcurrentLeave";
import EmployerClaimReview from "../../src/models/EmployerClaimReview";
import LeaveReason from "../../src/models/LeaveReason";
import createAbsencePeriod from "./createAbsencePeriod";
import dayjs from "dayjs";
import { set } from "lodash";

export class BaseMockBenefitsApplicationBuilder {
  employed() {
    set(this.claimAttrs, "employer_fein", "12-3456789");
    set(this.claimAttrs, "leave_details.employer_notified", true);
    set(this.claimAttrs, "hours_worked_per_week", 30);
    set(
      this.claimAttrs,
      "leave_details.employer_notification_date",
      "2022-01-01"
    );
    return this;
  }

  absenceId(absenceId = "NTN-111-ABS-01") {
    set(this.claimAttrs, "fineos_absence_id", absenceId);
    return this;
  }

  /**
   * @param {object} [attrs]
   * @returns {BaseMockBenefitsApplicationBuilder}
   */
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
            start_date: "2022-01-01",
            end_date: "2022-06-01",
          },
          leavePeriodAttrs
        )
      )
    );
    set(this.claimAttrs, "computed_start_dates", {
      other_reason: "2021-01-01",
      same_reason: "2021-01-01",
    });
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
            start_date: "2022-02-01",
            end_date: "2022-07-01",
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
    set(this.claimAttrs, "computed_start_dates", {
      other_reason: "2021-01-01",
      same_reason: "2021-01-01",
    });
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
            start_date: "2022-02-01",
            end_date: "2022-07-01",
          },
          leavePeriodAttrs
        )
      )
    );
    set(this.claimAttrs, "computed_start_dates", {
      other_reason: "2021-01-01",
      same_reason: "2021-01-01",
    });
    return this;
  }

  bondingLeaveReason() {
    set(this.claimAttrs, "leave_details.reason", LeaveReason.bonding);
    return this;
  }

  caringLeaveReason(attrs = {}) {
    set(this.claimAttrs, "leave_details.reason", LeaveReason.care);
    set(this.claimAttrs, "leave_details.caring_leave_metadata", {
      family_member_date_of_birth: "****-10-14",
      family_member_first_name: "Luther",
      family_member_middle_name: "James",
      family_member_last_name: "Toggle",
      relationship_to_caregiver: "Child",
      ...attrs,
    });
    return this;
  }

  medicalLeaveReason() {
    set(this.claimAttrs, "leave_details.reason", LeaveReason.medical);
    return this;
  }

  pregnancyLeaveReason() {
    set(this.claimAttrs, "leave_details.reason", LeaveReason.pregnancy);
    set(this.claimAttrs, "leave_details.pregnant_or_recent_birth", true);
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
              income_end_date: "2022-01-01",
              income_start_date: "2022-01-30",
              income_type: OtherIncomeType.otherEmployer,
            }),
          ]
    );
    set(this.claimAttrs, "has_other_incomes", true);
    return this;
  }

  otherIncomeFromUnemployment() {
    set(this.claimAttrs, "other_incomes", [
      new OtherIncome({
        income_amount_dollars: 125,
        income_amount_frequency: OtherIncomeFrequency.weekly,
        income_end_date: "2022-01-01",
        income_start_date: "2022-01-30",
        income_type: OtherIncomeType.unemployment,
      }),
    ]);
    set(this.claimAttrs, "has_other_incomes", true);
    return this;
  }

  concurrentLeave(attrs) {
    set(
      this.claimAttrs,
      "concurrent_leave",
      attrs
        ? new ConcurrentLeave(attrs)
        : new ConcurrentLeave({
            is_for_current_employer: true,
            leave_start_date: "2022-01-01",
            leave_end_date: "2022-03-01",
          })
    );

    if (this instanceof MockBenefitsApplicationBuilder) {
      // only the MockBenefitsApplicationBuilder has this attr, MockEmployerClaimBuilder does not
      set(this.claimAttrs, "has_concurrent_leave", true);
    }

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
              benefit_type: EmployerBenefitType.familyOrMedicalLeave,
              employer_benefit_id: 1,
              is_full_salary_continuous: false,
            }),
            new EmployerBenefit({
              benefit_type: EmployerBenefitType.familyOrMedicalLeave,
              employer_benefit_id: 2,
              is_full_salary_continuous: false,
            }),
            new EmployerBenefit({
              benefit_end_date: "2022-02-01",
              benefit_start_date: "2022-01-01",
              benefit_type: EmployerBenefitType.shortTermDisability,
              employer_benefit_id: 3,
              is_full_salary_continuous: true,
            }),
            new EmployerBenefit({
              benefit_type: EmployerBenefitType.permanentDisability,
              employer_benefit_id: 4,
              is_full_salary_continuous: false,
            }),
          ]
    );

    if (this instanceof MockBenefitsApplicationBuilder) {
      // only the MockBenefitsApplicationBuilder has this attr, MockEmployerClaimBuilder does not
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
export class MockEmployerClaimBuilder extends BaseMockBenefitsApplicationBuilder {
  constructor(middleName = "") {
    super();
    // Defaults, can be overridden by calling instance methods
    this.claimAttrs = {
      absence_periods: [],
      computed_start_dates: {
        other_reason: "2021-02-01",
        same_reason: "2021-02-01",
      },
      employer_dba: "Work Inc.",
      employer_id: "dda903f-f093f-ff900",
      first_name: "Jane",
      middle_name: middleName,
      last_name: "Doe",
      date_of_birth: "****-07-17",
      tax_identifier: "***-**-1234",
      fineos_absence_id: "NTN-111-ABS-01",
      previous_leaves: [],
      managed_requirements: [],
    };
  }

  /**
   * @returns {MockEmployerClaimBuilder}
   */
  continuousAbsencePeriod() {
    set(this.claimAttrs, "absence_periods", [
      ...this.claimAttrs.absence_periods,
      createAbsencePeriod({
        absence_period_end_date: "2022-04-01",
        absence_period_start_date: "2022-01-01",
        period_type: "Continuous",
        reason: LeaveReason.medical,
        request_decision: "Pending",
      }),
    ]);
    return this;
  }

  /**
   * @returns {MockEmployerClaimBuilder}
   */
  reducedScheduleAbsencePeriod() {
    set(this.claimAttrs, "absence_periods", [
      ...this.claimAttrs.absence_periods,
      createAbsencePeriod({
        absence_period_end_date: "2022-07-01",
        absence_period_start_date: "2022-05-01",
        period_type: "Reduced Schedule",
        reason: LeaveReason.medical,
        request_decision: "Pending",
      }),
    ]);
    return this;
  }

  /**
   * @returns {MockEmployerClaimBuilder}
   */
  intermittentAbsencePeriod() {
    set(this.claimAttrs, "absence_periods", [
      ...this.claimAttrs.absence_periods,
      createAbsencePeriod({
        absence_period_end_date: "2022-07-01",
        absence_period_start_date: "2022-02-01",
        period_type: "Intermittent",
        reason: LeaveReason.medical,
        request_decision: "Pending",
      }),
    ]);
    return this;
  }

  /**
   * @returns {MockEmployerClaimBuilder}
   */
  pendingAbsencePeriod() {
    set(this.claimAttrs, "absence_periods", [
      ...this.claimAttrs.absence_periods,
      createAbsencePeriod({
        request_decision: "Pending",
        absence_period_end_date: "2022-07-01",
        absence_period_start_date: "2022-02-01",
        period_type: "Continuous",
        reason: LeaveReason.medical,
      }),
    ]);
    return this;
  }

  /**
   * @returns {MockEmployerClaimBuilder}
   */
  completed(isIntermittent = false) {
    this.employed();
    this.address();
    if (isIntermittent) {
      this.intermittentAbsencePeriod();
    } else {
      this.continuousAbsencePeriod();
      this.reducedScheduleAbsencePeriod();
    }
    this.employerBenefit();
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
   * claim with open managed requirements and non-final absence period
   * @returns {MockEmployerClaimBuilder}
   */
  reviewable(date) {
    this.pendingAbsencePeriod();
    set(this.claimAttrs, "managed_requirements", [
      {
        follow_up_date: date || dayjs().add(10, "day").format("YYYY-MM-DD"),
        status: "Open",
      },
    ]);
    return this;
  }

  /**
   * claim with completed managed requirements
   * @returns {MockEmployerClaimBuilder}
   */
  reviewed() {
    set(this.claimAttrs, "managed_requirements", [
      {
        responded_at: "2022-02-02",
        status: "Complete",
      },
    ]);
    return this;
  }

  /**
   * @returns {MockEmployerClaimBuilder}
   */
  previousLeaves(attrs) {
    set(
      this.claimAttrs,
      "previous_leaves",
      attrs
        ? attrs.map((attr) => new PreviousLeave(attr))
        : [
            new PreviousLeave({
              is_for_current_employer: true,
              leave_minutes: 2400,
              leave_reason: PreviousLeaveReason.serviceMemberFamily,
              leave_start_date: "2020-03-01",
              leave_end_date: "2020-03-06",
              previous_leave_id: 0,
              type: PreviousLeaveType.otherReason,
              worked_per_week_minutes: 1440,
            }),
            new PreviousLeave({
              is_for_current_employer: true,
              leave_minutes: 4800,
              leave_reason: PreviousLeaveReason.bonding,
              leave_start_date: "2020-05-01",
              leave_end_date: "2020-05-10",
              previous_leave_id: 1,
              type: PreviousLeaveType.sameReason,
              worked_per_week_minutes: 960,
            }),
          ]
    );
    return this;
  }

  /**
   * Todo(EMPLOYER-1453): remove V1 eform functionality
   * @returns {MockEmployerClaimBuilder}
   */
  eformsV1() {
    set(this.claimAttrs, "uses_second_eform_version", false);
    return this;
  }

  /**
   * Todo(EMPLOYER-1453): remove V1 eform functionality
   * @returns {MockEmployerClaimBuilder}
   */
  eformsV2() {
    set(this.claimAttrs, "uses_second_eform_version", true);
    return this;
  }

  /**
   * @returns {EmployerClaimReview}
   */
  create() {
    return new EmployerClaimReview(this.claimAttrs);
  }
}

/**
 * A class that has chainable functions for conveniently creating mock claims
 * with prefilled data. Chain together multiple function calls, then call
 * the `create` function at the end to get the Claim object.
 * @class
 * @example
 *  new MockBenefitsApplicationBuilder()
 *    .continuous()
 *    .intermittent()
 *    .create();
 */
export class MockBenefitsApplicationBuilder extends BaseMockBenefitsApplicationBuilder {
  constructor() {
    super();
    this.claimAttrs = {
      application_id: "mock_application_id",
      status: BenefitsApplicationStatus.started,
      computed_start_dates: {},
      leave_details: {},
    };
  }

  /**
   * @returns {MockBenefitsApplicationBuilder}
   */
  id(application_id) {
    set(this.claimAttrs, "application_id", application_id);
    return this;
  }

  /**
   * @param {object} [leavePeriodAttrs]
   * @returns {MockBenefitsApplicationBuilder}
   */
  continuous(leavePeriodAttrs = {}) {
    set(this.claimAttrs, "has_continuous_leave_periods", true);
    super.continuous(leavePeriodAttrs);
    return this;
  }

  /**
   * Sets payment method to paper check
   * @returns {MockBenefitsApplicationBuilder}
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
   * @returns {MockBenefitsApplicationBuilder}
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
   * @returns {MockBenefitsApplicationBuilder}
   */
  hasOtherId() {
    set(this.claimAttrs, "has_state_id", false);
    return this;
  }

  /**
   * @returns {MockBenefitsApplicationBuilder}
   */
  hasStateId() {
    set(this.claimAttrs, "has_state_id", true);
    set(this.claimAttrs, "mass_id", "*********");
    return this;
  }

  /**
   * @param {object} [leavePeriodAttrs]
   * @returns {MockBenefitsApplicationBuilder}
   */
  intermittent(leavePeriodAttrs = {}) {
    set(this.claimAttrs, "has_intermittent_leave_periods", true);
    super.intermittent(leavePeriodAttrs);
    return this;
  }

  /**
   * @param {object} [leavePeriodAttrs]
   * @returns {MockBenefitsApplicationBuilder}
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
   * @returns {MockBenefitsApplicationBuilder}
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
   * @returns {MockBenefitsApplicationBuilder}
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
   * @returns {MockBenefitsApplicationBuilder}
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
   * @returns {MockBenefitsApplicationBuilder}
   */
  hasFutureChild() {
    set(this.claimAttrs, "leave_details.has_future_child_date", true);
    return this;
  }

  /**
   * @returns {MockBenefitsApplicationBuilder}
   */
  employed() {
    set(this.claimAttrs, "employment_status", EmploymentStatus.employed);
    super.employed();
    return this;
  }

  /**
   *
   * @returns {MockBenefitsApplicationBuilder}
   */
  previousLeavesSameReason(attrs) {
    set(this.claimAttrs, "has_previous_leaves_same_reason", true);
    set(
      this.claimAttrs,
      "previous_leaves_same_reason",
      attrs
        ? attrs.map(
            (attr) =>
              new PreviousLeave({ ...attr, type: PreviousLeaveType.sameReason })
          )
        : [
            new PreviousLeave({
              is_for_current_employer: true,
              leave_end_date: "2022-05-01",
              leave_start_date: "2022-07-01",
              leave_minutes: 20 * 60,
              leave_reason: null,
              type: PreviousLeaveType.sameReason,
              worked_per_week_minutes: 40 * 60,
            }),
          ]
    );
    return this;
  }

  /**
   *
   * @returns {MockClaimBuilder}
   */
  previousLeavesOtherReason(attrs) {
    set(this.claimAttrs, "has_previous_leaves_other_reason", true);
    set(
      this.claimAttrs,
      "previous_leaves_other_reason",
      attrs
        ? attrs.map(
            (attr) =>
              new PreviousLeave({
                ...attr,
                type: PreviousLeaveType.otherReason,
              })
          )
        : [
            new PreviousLeave({
              is_for_current_employer: true,
              leave_end_date: "2022-05-01",
              leave_start_date: "2022-07-01",
              leave_minutes: 20 * 60,
              leave_reason: PreviousLeaveReason.care,
              type: PreviousLeaveType.otherReason,
              worked_per_week_minutes: 40 * 60,
            }),
          ]
    );
    return this;
  }

  /**
   * @returns {MockBenefitsApplicationBuilder}
   */
  noOtherLeave() {
    set(this.claimAttrs, "has_employer_benefits", false);
    set(this.claimAttrs, "has_concurrent_leave", false);
    set(this.claimAttrs, "has_previous_leaves_same_reason", false);
    set(this.claimAttrs, "has_previous_leaves_other_reason", false);
    this.noOtherIncomes();
    return this;
  }

  noOtherIncomes() {
    set(this.claimAttrs, "has_other_incomes", false);
    return this;
  }

  // TODO (CP-2354) Remove this once there are no submitted claims with null Other Leave data
  nullOtherLeave() {
    set(this.claimAttrs, "has_employer_benefits", null);
    set(this.claimAttrs, "has_concurrent_leave", null);
    set(this.claimAttrs, "has_previous_leaves_same_reason", null);
    set(this.claimAttrs, "has_previous_leaves_other_reason", null);
    set(this.claimAttrs, "has_other_incomes", null);
    return this;
  }

  /**
   * @returns {MockBenefitsApplicationBuilder}
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
   * @returns {MockBenefitsApplicationBuilder}
   */
  notNotifiedEmployer() {
    set(this.claimAttrs, "leave_details.employer_notified", false);
    set(this.claimAttrs, "leave_details.employer_notification_date", null);
    return this;
  }

  /**
   * @returns {MockBenefitsApplicationBuilder}
   */
  pregnant() {
    set(this.claimAttrs, "leave_details.pregnant_or_recent_birth", true);
    return this;
  }

  /**
   * @returns {MockBenefitsApplicationBuilder}
   */
  employerOrganizationUnits(units) {
    set(this.claimAttrs, "employer_organization_units", units);
    return this;
  }

  /**
   * @returns {MockBenefitsApplicationBuilder}
   */
  employeeOrganizationUnits(units) {
    set(this.claimAttrs, "employee_organization_units", units);
    return this;
  }

  /**
   * All required data is present but the claim hasn't been marked
   * as Completed yet in the API
   * @returns {MockBenefitsApplicationBuilder}
   */
  complete() {
    this.submitted();
    this.paymentPrefSubmitted();
    this.taxPrefSubmitted();
    return this;
  }

  /**
   * Claim has all required data and has been marked as completed in the API
   * @returns {MockBenefitsApplicationBuilder}
   */
  completed() {
    this.complete();
    set(this.claimAttrs, "status", BenefitsApplicationStatus.completed);

    return this;
  }

  /**
   * Part 1 steps are complete but not yet submitted to API
   * @param {object} [options]
   * @param {boolean} [options.excludeLeavePeriod]
   * @returns {MockBenefitsApplicationBuilder}
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
   * @returns {MockBenefitsApplicationBuilder}
   */
  submitted() {
    this.part1Complete();
    this.absenceId();
    set(this.claimAttrs, "status", BenefitsApplicationStatus.submitted);

    return this;
  }

  /**
   * Part 2 payment step is completed and submitted to API
   * @returns {MockBenefitsApplicationBuilder}
   */
  paymentPrefSubmitted() {
    this.submitted();
    this.directDeposit();
    set(this.claimAttrs, "has_submitted_payment_preference", true);

    return this;
  }

  /**
   * Part 2 tax preference step is completed and submitted to API
   * @returns {MockBenefitsApplicationBuilder}
   */
  taxPrefSubmitted(selection = false) {
    this.submitted();
    set(this.claimAttrs, "is_withholding_tax", selection);

    return this;
  }

  /**
   * @param {object} [attrs] Address object
   * @returns {MockBenefitsApplicationBuilder}
   */
  address(attrs) {
    set(this.claimAttrs, "has_mailing_address", false);
    super.address(attrs);
    return this;
  }

  /**
   * @param {object} [attrs] Address object
   * @returns {MockBenefitsApplicationBuilder}
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
   * @returns {MockBenefitsApplicationBuilder}
   */
  verifiedId(middleName) {
    set(this.claimAttrs, "first_name", "Jane");
    set(this.claimAttrs, "middle_name", middleName || "");
    set(this.claimAttrs, "last_name", "Doe");
    set(this.claimAttrs, "gender", "Woman");
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
   * @returns {MockBenefitsApplicationBuilder}
   */
  workPattern(attrs = {}) {
    set(this.claimAttrs, "work_pattern", new WorkPattern(attrs));

    return this;
  }

  /**
   * @returns {MockBenefitsApplicationBuilder}
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
   * @returns {MockBenefitsApplicationBuilder}
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
   * @param {string | null} [computed_earliest_submission_date]
   * @returns {MockBenefitsApplicationBuilder}
   */
  computedEarliestSubmissionDate(computed_earliest_submission_date = null) {
    set(
      this.claimAttrs,
      "computed_earliest_submission_date",
      computed_earliest_submission_date
    );
    return this;
  }

  /**
   * @param {string} [id]
   * @returns {MockBenefitsApplicationBuilder}
   */
  splitIntoApplicationId(id) {
    set(this.claimAttrs, "split_into_application_id", id);
    return this;
  }

  /**
   * @param {string} [id]
   * @returns {MockBenefitsApplicationBuilder}
   */
  splitFromApplicationId(id) {
    set(this.claimAttrs, "split_from_application_id", id);
    return this;
  }

  /**
   * @returns {BenefitsApplication}
   */
  create() {
    return new BenefitsApplication(this.claimAttrs);
  }
}
