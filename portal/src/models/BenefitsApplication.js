/* eslint sort-keys: ["error", "asc"] */
/**
 * @file Benefits application model and enum values
 */
import { compact, get, isNil, merge, sum, sumBy, zip, zipObject } from "lodash";
import BaseBenefitsApplication from "./BaseBenefitsApplication";
import BaseModel from "./BaseModel";
import { DateTime } from "luxon";
import LeaveReason from "./LeaveReason";
import assert from "assert";
import spreadMinutesOverWeek from "../utils/spreadMinutesOverWeek";

class BenefitsApplication extends BaseBenefitsApplication {
  get defaults() {
    return merge({
      ...super.defaults,
      employment_status: null,
      has_continuous_leave_periods: null,
      has_employer_benefits: null,
      has_intermittent_leave_periods: null,
      has_mailing_address: null,
      has_other_incomes: null,
      has_previous_leaves: null,
      has_previous_leaves_other_reason: null,
      has_previous_leaves_same_reason: null,
      has_reduced_schedule_leave_periods: null,
      has_state_id: null,
      has_submitted_payment_preference: null,
      leave_details: {
        caring_leave_metadata: null,
        child_birth_date: null,
        child_placement_date: null,
        employer_notified: null,
        has_future_child_date: null,
        pregnant_or_recent_birth: null,
        reason_qualifier: null,
      },
      // address object. See Address model
      mailing_address: null, // default value to null
      mass_id: null,
      // array of OtherIncome objects. See the OtherIncome model
      other_incomes: [],
      other_incomes_awaiting_approval: null,
      // See PaymentPreference model
      payment_preference: null,
      phone: {
        int_code: null,
        phone_number: null,
        phone_type: null, // PhoneType
      },
      previous_leaves_other_reason: [],
      previous_leaves_same_reason: [],
      work_pattern: null,
    });
  }

  /**
   * Determine if applicable leave period start date(s) are in the future.
   * @returns {boolean}
   */
  get isLeaveStartDateInFuture() {
    const startDates = compact([
      get(this, "leave_details.continuous_leave_periods[0].start_date"),
      get(this, "leave_details.intermittent_leave_periods[0].start_date"),
      get(this, "leave_details.reduced_schedule_leave_periods[0].start_date"),
    ]);

    if (!startDates.length) return false;

    const now = DateTime.local().toISODate();
    return startDates.every((startDate) => {
      // Compare the two dates lexicographically. This works since they're both in
      // ISO-8601 format, eg "2020-10-13"
      return startDate > now;
    });
  }

  /**
   * Check if Claim has been marked as completed yet.
   * @returns {boolean}
   */
  get isCompleted() {
    return this.status === ClaimStatus.completed;
  }

  /**
   * Determine if claim is a Medical Leave claim
   * @returns {boolean}
   */
  get isMedicalLeave() {
    return get(this, "leave_details.reason") === LeaveReason.medical;
  }

  /**
   * Determine if claim is a Caring Leave claim
   * @returns {boolean}
   */
  get isCaringLeave() {
    return get(this, "leave_details.reason") === LeaveReason.care;
  }

  /**
   * Check if Claim has been submitted yet. This affects the editability
   * of some fields, and as a result, the user experience.
   * @returns {boolean}
   */
  get isSubmitted() {
    return this.status === ClaimStatus.submitted;
  }
}

/**
 * Enums for the Application's `status` field
 * @enum {string}
 */
export const ClaimStatus = {
  // Submitted by the user (Step 2)
  completed: "Completed",
  // AKA: In Progress (Step 1)
  started: "Started",
  // Stored in the claims processing system (Step 3)
  submitted: "Submitted",
};

/**
 * Enums for the Application's `employment_status` field
 * @enum {string}
 */
export const EmploymentStatus = {
  employed: "Employed",
  selfEmployed: "Self-Employed",
  unemployed: "Unemployed",
};

/**
 * Enums for the Application's `leave_details.reason_qualifier` field
 * @enum {string}
 */
export const ReasonQualifier = {
  adoption: "Adoption",
  fosterCare: "Foster Care",
  newBorn: "Newborn",
};

export class ContinuousLeavePeriod extends BaseModel {
  get defaults() {
    return {
      end_date: null,
      leave_period_id: null,
      start_date: null,
    };
  }
}

export class IntermittentLeavePeriod extends BaseModel {
  get defaults() {
    return {
      // How many {days|hours} of work will you miss per absence?
      duration: null,
      // How long will an absence typically last?
      duration_basis: null,
      end_date: null,
      // Estimate how many absences {per week|per month|over the next 6 months}
      frequency: null,
      // Implied by input selection of "over the next 6 months"
      // and can only ever be equal to 6
      frequency_interval: null,
      // How often might you need to be absent from work?
      frequency_interval_basis: null,
      leave_period_id: null,
      start_date: null,
    };
  }
}

export class CaringLeaveMetadata extends BaseModel {
  get defaults() {
    return {
      family_member_date_of_birth: null,
      family_member_first_name: null,
      family_member_last_name: null,
      family_member_middle_name: null,
      relationship_to_caregiver: null,
    };
  }
}

export class WorkPattern extends BaseModel {
  constructor(attrs) {
    super(attrs);
    const work_pattern_days = get(attrs, "work_pattern_days");

    if (work_pattern_days) {
      // Defaults only override null or undefined values
      // We should also use defaults for empty work_pattern_days
      if (work_pattern_days.length === 0) {
        merge(this, { work_pattern_days: this.defaults.work_pattern_days });
      } else {
        assert(
          work_pattern_days.length === 7,
          `${work_pattern_days.length} work_pattern_days length must be 7. Consider using WorkPattern's static createWithWeek.`
        );
      }
    }
  }

  get defaults() {
    return {
      work_pattern_days: OrderedDaysOfWeek.map(
        (day_of_week) => new WorkPatternDay({ day_of_week, minutes: null })
      ),
      work_pattern_type: null,
    };
  }

  /**
   * Return total minutes worked for work pattern days. Returns null if no minutes are defined for work pattern days
   * @returns {(number|null)}
   */
  get minutesWorkedPerWeek() {
    const hasNoMinutes = this.work_pattern_days.every(
      (day) => day.minutes === null
    );
    if (hasNoMinutes) {
      return null;
    }

    return sumBy(this.work_pattern_days, "minutes");
  }

  /**
   * Create a WorkPattern with a week, splitting provided minutes across 7 work_pattern_days.
   * @param {number} minutesWorkedPerWeek - average minutes worked per week. Must be an integer. Will split minutes evenly across 7 day week
   * @param {WorkPattern} [workPattern] - optional, work pattern attributes to apply to new WorkPattern
   * @returns {WorkPattern}
   */
  static createWithWeek(minutesWorkedPerWeek, workPattern = {}) {
    assert(!isNil(minutesWorkedPerWeek));
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

export class WorkPatternDay extends BaseModel {
  get defaults() {
    return {
      day_of_week: null,
      // API represents hours in minutes
      minutes: null,
    };
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
};

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
};
export class ReducedScheduleLeavePeriod extends BaseModel {
  get defaults() {
    return {
      end_date: null,
      friday_off_minutes: null,
      leave_period_id: null,
      monday_off_minutes: null,
      saturday_off_minutes: null,
      start_date: null,
      sunday_off_minutes: null,
      thursday_off_minutes: null,
      tuesday_off_minutes: null,
      wednesday_off_minutes: null,
    };
  }

  /**
   * @returns {{ minutes: number, day_of_week: string }[]}
   */
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
   * @returns {number?} Sum of all *_off_minutes fields.
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
};

/**
 * Enums for caring leave's relationship to caregiver
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
};

/**
 * Enums for the Application's `work_pattern.work_pattern_type` field
 * @enum {string}
 */
export const WorkPatternType = {
  fixed: "Fixed",
  rotating: "Rotating",
  variable: "Variable",
};

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
];

/**
 * Enums for the Application's `work_pattern.work_pattern_days[].day_of_week` fields
 * Produces object: { sunday: "Sunday", monday: "Monday", ... }
 * @example DayOfWeek.sunday
 * @enum {string}
 */
export const DayOfWeek = zipObject(
  OrderedDaysOfWeek.map((day) => day.toLowerCase()),
  OrderedDaysOfWeek
);

export default BenefitsApplication;
