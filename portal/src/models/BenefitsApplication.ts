/**
 * @file Benefits application model and enum values
 */

import LeaveReason, { LeaveReasonType } from "./LeaveReason";
import { compact, get, merge, sum, sumBy, zip } from "lodash";

import Address from "./Address";
import BaseBenefitsApplication from "./BaseBenefitsApplication";
import ConcurrentLeave from "./ConcurrentLeave";
import EmployerBenefit from "./EmployerBenefit";
import OrganizationUnit from "./OrganizationUnit";
import OtherIncome from "./OtherIncome";
import PaymentPreference from "./PaymentPreference";
import PreviousLeave from "./PreviousLeave";
import { ValuesOf } from "../../types/common";
import assert from "assert";
import dayjs from "dayjs";
import isBlank from "../utils/isBlank";
import spreadMinutesOverWeek from "../utils/spreadMinutesOverWeek";

class BenefitsApplication extends BaseBenefitsApplication {
  application_id: string;
  fineos_absence_id: string | null = null;
  organization_unit_id: string | null = null;
  organization_unit_selection: "not_listed" | "not_selected" | null = null;

  first_name: string | null = null;
  middle_name: string | null = null;
  last_name: string | null = null;
  computed_earliest_submission_date: string | null = null;
  concurrent_leave: ConcurrentLeave | null = null;
  employer_benefits: EmployerBenefit[] = [];
  date_of_birth: string | null = null;
  employee_id: string | null = null;
  employer_fein: string | null = null;
  gender: ValuesOf<typeof Gender> | null = null;
  has_concurrent_leave: boolean | null = null;
  has_continuous_leave_periods: boolean | null = null;
  has_employer_benefits: boolean | null = null;
  has_intermittent_leave_periods: boolean | null = null;
  has_mailing_address: boolean | null = null;
  has_other_incomes: boolean | null = null;
  has_previous_leaves_other_reason: boolean | null = null;
  has_previous_leaves_same_reason: boolean | null = null;
  has_reduced_schedule_leave_periods: boolean | null = null;
  has_state_id: boolean | null = null;
  has_submitted_payment_preference: boolean | null = null;
  hours_worked_per_week: number | null = null;
  is_withholding_tax: boolean | null = null;
  mass_id: string | null = null;
  mailing_address: Address | null = null;
  other_incomes: OtherIncome[] = [];
  payment_preference: PaymentPreference | null = null;
  previous_leaves_other_reason: PreviousLeave[] = [];
  previous_leaves_same_reason: PreviousLeave[] = [];
  residential_address: Address = new Address({});
  tax_identifier: string | null = null;
  work_pattern: Partial<WorkPattern> | null = null;

  employment_status: ValuesOf<typeof EmploymentStatus> | null = null;

  computed_start_dates: {
    other_reason?: string | null;
    same_reason?: string | null;
  };

  leave_details: {
    continuous_leave_periods: ContinuousLeavePeriod[];
    intermittent_leave_periods: IntermittentLeavePeriod[];
    reduced_schedule_leave_periods: ReducedScheduleLeavePeriod[];
    employer_notified: boolean | null;
    employer_notification_date: string | null;
    caring_leave_metadata: CaringLeaveMetadata | null;
    child_birth_date: string | null;
    child_placement_date: string | null;
    has_future_child_date: boolean | null;
    pregnant_or_recent_birth: boolean | null;
    reason: ValuesOf<typeof LeaveReason> | null;
    reason_qualifier: ReasonQualifierEnum | null;
  };

  phone: {
    int_code: string | null;
    phone_number: string | null;
    phone_type: ValuesOf<typeof PhoneType> | null;
  };

  status: ValuesOf<typeof BenefitsApplicationStatus> | null = null;

  // Organization unit data selected by the user (used in review page)
  organization_unit: OrganizationUnit | null;

  // The list of organization units that we know are connected
  // to this employee based on their occupation and DUA data
  employee_organization_units: OrganizationUnit[] = [];

  // The list of organization units that are connected to this employer (in FINEOS)
  employer_organization_units: OrganizationUnit[] = [];

  constructor(attrs: Partial<BenefitsApplication>) {
    super();
    // Recursively merge with the defaults
    merge(this, attrs);
  }

  /**
   * Applications imported from Fineos as part of Channel Switching won't have
   * any caring leave metadata fields set.
   */
  get hasCaringLeaveMetadata(): boolean {
    return !isBlank(
      this.leave_details.caring_leave_metadata?.family_member_first_name
    );
  }

  /**
   * Determine if applicable leave period start date(s) are in the future.
   */
  get isLeaveStartDateInFuture() {
    const startDates: string[] = compact([
      get(this, "leave_details.continuous_leave_periods[0].start_date"),
      get(this, "leave_details.intermittent_leave_periods[0].start_date"),
      get(this, "leave_details.reduced_schedule_leave_periods[0].start_date"),
    ]);

    if (!startDates.length) return false;

    const now = dayjs().format("YYYY-MM-DD"); // current date in ISO 8601 string in local time (by default day.js parses in local time)
    return startDates.every((startDate) => {
      // Compare the two dates lexicographically. This works since they're both in
      // ISO-8601 format, eg "2020-10-13"
      return startDate > now;
    });
  }

  /**
   * Determine if the earliest possible application submission date is in the future (i.e., they must wait to submit their application).
   */
  get isEarliestSubmissionDateInFuture() {
    if (this.computed_earliest_submission_date === null) {
      return false;
    }

    const now = dayjs().format("YYYY-MM-DD");
    return this.computed_earliest_submission_date > now;
  }

  /**
   * Check if Claim has been marked as completed yet.
   */
  get isCompleted() {
    return this.status === BenefitsApplicationStatus.completed;
  }

  /**
   * Determine if claim is a Medical or Pregnancy leave claim
   */
  get isMedicalOrPregnancyLeave(): boolean {
    const reason: LeaveReasonType = get(this, "leave_details.reason");
    return reason === LeaveReason.medical || reason === LeaveReason.pregnancy;
  }

  /**
   * Determine if claim is a Caring Leave claim
   */
  get isCaringLeave(): boolean {
    return get(this, "leave_details.reason") === LeaveReason.care;
  }

  /**
   * Check if Claim has been submitted yet. This affects the editability
   * of some fields, and as a result, the user experience.
   */
  get isSubmitted() {
    return (
      this.status === BenefitsApplicationStatus.submitted ||
      this.status === BenefitsApplicationStatus.completed
    );
  }

  /**
   * Returns a list of the employer's organization units
   * except for the ones connected to the employee
   */
  get extraOrgUnits() {
    return this.employer_organization_units.filter(
      (o) =>
        !this.employee_organization_units
          .map((o) => o.organization_unit_id)
          .includes(o.organization_unit_id)
    );
  }

  /**
   * Returns earliest start date across all leave periods
   */
  get leaveStartDate() {
    const periods = [
      get(this, "leave_details.continuous_leave_periods"),
      get(this, "leave_details.intermittent_leave_periods"),
      get(this, "leave_details.reduced_schedule_leave_periods"),
    ].flat();

    const startDates: string[] = compact(periods)
      .map((period) => period.start_date)
      .sort();

    if (!startDates.length) return null;

    return startDates[0];
  }

  /**
   * Returns latest end date across all leave periods
   */
  get leaveEndDate() {
    const periods = [
      get(this, "leave_details.continuous_leave_periods"),
      get(this, "leave_details.intermittent_leave_periods"),
      get(this, "leave_details.reduced_schedule_leave_periods"),
    ].flat();

    const endDates: string[] = compact(periods)
      .map((period) => period.end_date)
      .sort();

    if (!endDates.length) return null;

    return endDates[endDates.length - 1];
  }
}

/**
 * Enums for the Application's `status` field
 * @enum {string}
 */
export const BenefitsApplicationStatus = {
  // Submitted by the user (Step 2)
  completed: "Completed",
  // AKA: In Progress (Step 1)
  started: "Started",
  // Stored in the claims processing system (Step 3)
  submitted: "Submitted",
  // User not found - No link between employee and employer
  // User completed Step 1 and part of Step 2 along with additional information to help make a manual match
  inReview: "In Review",
} as const;

/**
 * Enums for the Application's `employment_status` field
 * @enum {string}
 */
export const EmploymentStatus = {
  employed: "Employed",
  selfEmployed: "Self-Employed",
  unemployed: "Unemployed",
} as const;

/**
 * Enums for the Application's `leave_details.reason_qualifier` field
 * @enum {string}
 */
export const ReasonQualifier = {
  adoption: "Adoption",
  fosterCare: "Foster Care",
  newBorn: "Newborn",
} as const;

export type ReasonQualifierEnum = ValuesOf<typeof ReasonQualifier>;

export class ContinuousLeavePeriod {
  leave_period_id: string | null = null;
  end_date: string | null = null;
  start_date: string | null = null;

  constructor(attrs: Partial<ContinuousLeavePeriod>) {
    Object.assign(this, attrs);
  }
}

export class IntermittentLeavePeriod {
  leave_period_id: string | null = null;
  start_date: string | null = null;
  end_date: string | null = null;
  // How many {days|hours} of work will you miss per absence?
  duration: number | null = null;
  // How long will an absence typically last?
  duration_basis: ValuesOf<typeof DurationBasis> | null = null;

  // Estimate how many absences {per week|per month|over the next 6 months}
  frequency: number | null = null;
  // Implied by input selection of "over the next 6 months"
  // and can only ever be equal to 6
  frequency_interval: number | null = null;
  // How often might you need to be absent from work?
  frequency_interval_basis: ValuesOf<typeof FrequencyIntervalBasis> | null =
    null;

  constructor(attrs: Partial<IntermittentLeavePeriod>) {
    Object.assign(this, attrs);
  }
}

export class CaringLeaveMetadata {
  family_member_date_of_birth: string | null = null;
  family_member_first_name: string | null = null;
  family_member_last_name: string | null = null;
  family_member_middle_name: string | null = null;
  relationship_to_caregiver: ValuesOf<typeof RelationshipToCaregiver> | null =
    null;

  constructor(attrs: Partial<CaringLeaveMetadata>) {
    Object.assign(this, attrs);
  }
}

export class WorkPattern {
  work_pattern_days: WorkPatternDay[] | null = [];
  work_pattern_type: ValuesOf<typeof WorkPatternType> | null = null;

  constructor(attrs: Partial<WorkPattern>) {
    Object.assign(this, attrs);

    if (!this.work_pattern_days || !this.work_pattern_days.length) {
      this.work_pattern_days = OrderedDaysOfWeek.map(
        (day_of_week) => new WorkPatternDay({ day_of_week, minutes: null })
      );
    }

    assert(
      this.work_pattern_days.length === 7,
      `${this.work_pattern_days.length} work_pattern_days length must be 7. Consider using WorkPattern's static createWithWeek.`
    );
  }

  /**
   * Return total minutes worked for work pattern days. Returns null if no minutes are defined for work pattern days
   */
  get minutesWorkedPerWeek() {
    const hasNoMinutes =
      this.work_pattern_days &&
      this.work_pattern_days.every((day) => day.minutes === null);
    if (hasNoMinutes) {
      return null;
    }

    return sumBy(this.work_pattern_days, "minutes");
  }

  /**
   * Create a WorkPattern with a week, splitting provided minutes across 7 work_pattern_days.
   * @param minutesWorkedPerWeek - average minutes worked per week. Must be an integer. Will split minutes evenly across 7 day week
   * @param workPattern - work pattern attributes to apply to new WorkPattern
   */
  static createWithWeek(
    minutesWorkedPerWeek: number,
    workPattern: WorkPattern | { [key: string]: never } = {}
  ) {
    const minutesOverWeek = spreadMinutesOverWeek(minutesWorkedPerWeek);

    const newWeek = zip(OrderedDaysOfWeek, minutesOverWeek).map(
      ([day_of_week, minutes]) =>
        new WorkPatternDay({
          day_of_week,
          minutes,
        })
    );

    return new WorkPattern({
      ...workPattern,
      work_pattern_days: newWeek,
    });
  }
}

export class WorkPatternDay {
  day_of_week: typeof OrderedDaysOfWeek[number] | null = null;
  // API represents hours in minutes
  minutes: number | null = null;

  constructor(attrs: Partial<WorkPatternDay>) {
    Object.assign(this, attrs);
  }
}

/**
 * Enums for the Application's `intermittent_leave_periods[].frequency_interval_basis` field
 * @enum {string}
 */
export const FrequencyIntervalBasis = {
  // Days is also a valid enum in the API, however the Portal
  // doesn't offer this as an option to the user
  // days: "Days",
  months: "Months",
  weeks: "Weeks",
} as const;

/**
 * Enums for the Application's `intermittent_leave_periods[].duration_basis` field
 * @enum {string}
 */
export const DurationBasis = {
  days: "Days",
  hours: "Hours",
  // Minutes is also a valid enum in the API, however the Portal
  // doesn't offer this as an option to the user
  // minutes: "Minutes",
} as const;

export class ReducedScheduleLeavePeriod {
  leave_period_id: string | null = null;
  start_date: string | null = null;
  end_date: string | null = null;
  sunday_off_minutes: number | null = null;
  monday_off_minutes: number | null = null;
  tuesday_off_minutes: number | null = null;
  wednesday_off_minutes: number | null = null;
  thursday_off_minutes: number | null = null;
  friday_off_minutes: number | null = null;
  saturday_off_minutes: number | null = null;

  constructor(attrs: Partial<ReducedScheduleLeavePeriod>) {
    Object.assign(this, attrs);
  }

  get days() {
    return [
      {
        day_of_week: DayOfWeek.sunday,
        minutes: this.sunday_off_minutes,
      },
      {
        day_of_week: DayOfWeek.monday,
        minutes: this.monday_off_minutes,
      },
      {
        day_of_week: DayOfWeek.tuesday,
        minutes: this.tuesday_off_minutes,
      },
      {
        day_of_week: DayOfWeek.wednesday,
        minutes: this.wednesday_off_minutes,
      },
      {
        day_of_week: DayOfWeek.thursday,
        minutes: this.thursday_off_minutes,
      },
      {
        day_of_week: DayOfWeek.friday,
        minutes: this.friday_off_minutes,
      },
      {
        day_of_week: DayOfWeek.saturday,
        minutes: this.saturday_off_minutes,
      },
    ];
  }

  /**
   */
  get totalMinutesOff() {
    const fieldsWithMinutes = compact([
      this.friday_off_minutes,
      this.monday_off_minutes,
      this.saturday_off_minutes,
      this.sunday_off_minutes,
      this.thursday_off_minutes,
      this.tuesday_off_minutes,
      this.wednesday_off_minutes,
    ]);

    if (fieldsWithMinutes.length) {
      return sum(fieldsWithMinutes);
    }

    return null;
  }
}

/**
 * Enums for the Application's `phone.phone_type` field
 * @enum {string}
 */
export const PhoneType = {
  cell: "Cell",
  phone: "Phone",
} as const;

/* Enums for claimant gender options
 * @enum {string}
 */
export const Gender = {
  genderNotListed: "Gender not listed",
  man: "Man",
  nonbinary: "Non-binary",
  preferNotToAnswer: "Prefer not to answer",
  woman: "Woman",
} as const;

/* Enums for caring leave's relationship to caregiver
 * @enum {string}
 */
export const RelationshipToCaregiver = {
  child: "Child",
  grandchild: "Grandchild",
  grandparent: "Grandparent",
  inlaw: "Inlaw",
  other: "Other",
  otherFamilyMember: "Other Family Member",
  parent: "Parent",
  serviceMember: "Service Member",
  sibling: "Sibling - Brother/Sister",
  spouse: "Spouse",
} as const;

/**
 * Enums for the Application's `work_pattern.work_pattern_type` field
 * @enum {string}
 */
export const WorkPatternType = {
  fixed: "Fixed",
  rotating: "Rotating",
  variable: "Variable",
} as const;

/**
 * Ordered days of the week
 */
export const OrderedDaysOfWeek = [
  "Sunday",
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
  "Saturday",
] as const;

/**
 * Enums for the Application's `work_pattern.work_pattern_days[].day_of_week` fields
 * Produces object: { sunday: "Sunday", monday: "Monday", ... }
 * @example DayOfWeek.sunday
 * @enum {string}
 */
/* eslint-disable sort-keys */
export const DayOfWeek = {
  sunday: "Sunday",
  monday: "Monday",
  tuesday: "Tuesday",
  wednesday: "Wednesday",
  thursday: "Thursday",
  friday: "Friday",
  saturday: "Saturday",
} as const;

export default BenefitsApplication;
