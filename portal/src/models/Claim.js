/* eslint sort-keys: ["error", "asc"] */
/**
 * @file Benefits application model and enum values
 */
import {
  compact,
  get,
  groupBy,
  merge,
  sortBy,
  sum,
  sumBy,
  zip,
  zipObject,
} from "lodash";
import BaseClaim from "./BaseClaim";
import BaseModel from "./BaseModel";
import { DateTime } from "luxon";
import assert from "assert";
import spreadMinutesOverWeek from "../utils/spreadMinutesOverWeek";

class Claim extends BaseClaim {
  get defaults() {
    return merge({
      ...super.defaults,
      employment_status: null,
      has_continuous_leave_periods: null,
      has_intermittent_leave_periods: null,
      has_mailing_address: null,
      has_reduced_schedule_leave_periods: null,
      has_state_id: null,
      leave_details: {
        child_birth_date: null,
        child_placement_date: null,
        employer_notified: null,
        pregnant_or_recent_birth: null,
        reason_qualifier: null,
      },
      // address object. See Address model
      mailing_address: null, // default value to null
      mass_id: null,
      // array of OtherIncome objects. See the OtherIncome model
      other_incomes: [],
      payment_preferences: [
        {
          // Fields for ACH details
          account_details: {
            account_number: null,
            account_type: null, // PaymentAccountType
            routing_number: null,
          },
          payment_method: null, // PaymentPreferenceMethod
          payment_preference_id: null,
        },
      ],
      /**
       * Fields within the `temp` object haven't been connected to the API yet, and
       * should have a ticket in Jira related to eventually moving them out of
       * this temporary space.
       */
      temp: {
        // TODO (CP-567): this field doesn't exist in the API yet
        has_employer_benefits: null,
        // TODO (CP-567): this field doesn't exist in the API yet
        has_other_incomes: null,
        // TODO (CP-567): this field doesn't exist in the API yet
        has_previous_leaves: null,
      },
      work_pattern: null,
    });
  }

  /**
   * Determine if claim is a Bonding Leave claim
   * @returns {boolean}
   */
  get isBondingLeave() {
    return get(this, "leave_details.reason") === LeaveReason.bonding;
  }

  /**
   * Determine if the claim is a Bonding Leave claim where the birth or
   * placement date is in the future.
   * @returns {boolean}
   */
  get isChildDateInFuture() {
    if (!this.isBondingLeave) return false;

    const birthOrPlacementDate =
      get(this, "leave_details.child_birth_date") ||
      get(this, "leave_details.child_placement_date");
    // Assumes that the birth/placement date is in the same timezone as the user's browser
    const now = DateTime.local().toISODate();

    // Compare the two dates lexicographically. This works since they're both in
    // ISO-8601 format, eg "2020-10-13"
    return birthOrPlacementDate > now;
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
 * Enums for the Application's `leave_details.reason` field
 * @enum {string}
 */
export const LeaveReason = {
  // TODO (CP-534): We need to map some of these to the correct API fields,
  // once those enum values exist within the API
  activeDutyFamily: "Care For A Family Member",
  bonding: "Child Bonding",
  medical: "Serious Health Condition - Employee",
  serviceMemberFamily: "Pregnancy/Maternity",
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

export class WorkPattern extends BaseModel {
  constructor(attrs) {
    const work_pattern_days = get(attrs, "work_pattern_days");

    if (work_pattern_days) {
      assert(
        work_pattern_days.length % 7 === 0,
        "work_pattern_days length must be a multiple of 7. Consider using WorkPattern's static `addWeek` or `removeWeek` methods."
      );
    }

    super(attrs);
  }

  get defaults() {
    return {
      pattern_start_date: null,
      work_pattern_days: [],
      work_pattern_type: null,
      work_week_starts: "Sunday",
    };
  }

  /**
   * Return work_pattern_days grouped by week_number.
   * @returns {Array.<WorkPatternDay[]>}
   */
  get weeks() {
    const workPatternDays = sortBy([...this.work_pattern_days], (day) =>
      OrderedDaysOfWeek.indexOf(day.day_of_week)
    );
    return Object.values(groupBy(workPatternDays, "week_number"));
  }

  /**
   * Return array with total minutes worked each week
   * @returns {number[]}
   */
  get minutesWorkedEachWeek() {
    return this.weeks.map((days) => sumBy(days, "minutes"));
  }

  /**
   * Add a 7 day week to work_pattern_days.
   * @param {WorkPattern} workPattern - instance of a WorkPattern
   * @param {number} [minutesWorkedPerWeek] - average minutes worked per week. Must be an integer. If provided, will split minutes evenly across 7 day week
   * @returns {WorkPattern}
   */
  static addWeek(workPattern, minutesWorkedPerWeek = 0) {
    // TODO (CP-1336): Move away from defaulting minutesWorkedPerWeek to 0
    const minutesOverWeek = spreadMinutesOverWeek(minutesWorkedPerWeek);

    const newWeek = zip(OrderedDaysOfWeek, minutesOverWeek).map(
      ([day_of_week, minutes]) =>
        new WorkPatternDay({
          day_of_week,
          minutes,
          week_number: workPattern.weeks.length + 1,
        })
    );

    return new WorkPattern({
      ...workPattern,
      work_pattern_days: [...workPattern.work_pattern_days, ...newWeek],
    });
  }

  /**
   * Update minutes of a 7 day week.
   * @param {WorkPattern} workPattern - instance of a WorkPattern
   * @param {number} weekNumber - number of the week to update
   * @param {number} minutesWorkedPerWeek - average minutes worked per week. Must be an integer. If provided, will split minutes evenly across 7 day week
   * @returns {WorkPattern}
   */
  static updateWeek(workPattern, weekNumber, minutesWorkedPerWeek) {
    const minutesOverWeek = spreadMinutesOverWeek(minutesWorkedPerWeek);
    const weeks = workPattern.weeks;
    const i = weekNumber - 1;
    assert(weeks[i]);

    weeks[i] = zip(weeks[i], minutesOverWeek).map(
      ([day, minutes]) =>
        new WorkPatternDay({
          ...day,
          minutes,
        })
    );

    return new WorkPattern({
      ...workPattern,
      work_pattern_days: [...weeks.flat()],
    });
  }

  /**
   * Remove a 7 day week from work_pattern_days by week_number
   * @param {WorkPattern} workPattern - instance of a WorkPattern
   * @param {number} weekNumber - week_number to be removed
   * @returns {WorkPattern}
   */
  static removeWeek(workPattern, weekNumber) {
    const weeks = workPattern.weeks;
    weeks.splice(weekNumber - 1, 1);

    const work_pattern_days = weeks.flatMap((week, i) =>
      week.map((day) => new WorkPatternDay({ ...day, week_number: i + 1 }))
    );

    return new WorkPattern({
      ...workPattern,
      work_pattern_days,
    });
  }
}

export class WorkPatternDay extends BaseModel {
  get defaults() {
    return {
      day_of_week: null,
      // API represents hours in minutes
      minutes: null,
      // an integer between 1 and 4
      week_number: null,
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
 * Enums for the Application's `payment_preferences[].account_details.account_type` field
 * @enum {string}
 */
export const PaymentAccountType = {
  checking: "Checking",
  savings: "Savings",
};

/**
 * Enums for the Application's `payment_preferences[].payment_method` field
 * @enum {string}
 */
export const PaymentPreferenceMethod = {
  ach: "ACH",
  check: "Check",
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
 * Enums for the Application's `work_pattern.work_week_starts` and `work_pattern.work_pattern_days[].day_of_week` fields
 * Produces object: { sunday: "Sunday", monday: "Monday", ... }
 * @enum {string}
 */
export const DayOfWeek = zipObject(
  OrderedDaysOfWeek.map((day) => day.toLowerCase()),
  OrderedDaysOfWeek
);

export default Claim;
