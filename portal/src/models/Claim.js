/* eslint sort-keys: ["error", "asc"] */
/**
 * @file Benefits application model and enum values
 */
import { compact, get, groupBy, sortBy, sumBy, zip, zipObject } from "lodash";
import Address from "./Address";
import BaseModel from "./BaseModel";
import { DateTime } from "luxon";
import assert from "assert";
import convertMinutesToHours from "../utils/convertMinutesToHours";

class Claim extends BaseModel {
  get defaults() {
    return {
      application_id: null,
      created_at: null,
      date_of_birth: null,
      // array of EmployerBenefit objects. See the EmployerBenefit model
      employer_benefits: [],
      employer_fein: null,
      employment_status: null,
      fineos_absence_id: null,
      first_name: null,
      has_continuous_leave_periods: null,
      has_intermittent_leave_periods: null,
      has_mailing_address: null,
      has_reduced_schedule_leave_periods: null,
      has_state_id: null,
      hours_worked_per_week: null,
      last_name: null,
      leave_details: {
        child_birth_date: null,
        child_placement_date: null,
        continuous_leave_periods: null,
        employer_notification_date: null,
        employer_notified: null,
        intermittent_leave_periods: null,
        pregnant_or_recent_birth: null,
        reason: null,
        reason_qualifier: null,
        reduced_schedule_leave_periods: null,
      },
      // address object. See Address model
      mailing_address: null,
      mass_id: null,
      middle_name: null,
      // array of OtherIncome objects. See the OtherIncome model
      other_incomes: [],
      // array of PreviousLeave objects. See the PreviousLeave model
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
      previous_leaves: [],
      residential_address: new Address(),
      status: null,
      tax_identifier: null,
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
    };
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
   * Determine if claim is a continuous leave claim
   * @returns {boolean}
   */
  get isContinuous() {
    return !!get(this, "leave_details.continuous_leave_periods[0]");
  }

  /**
   * Determine if claim is an intermittent leave claim
   * @returns {boolean}
   */
  get isIntermittent() {
    return !!get(this, "leave_details.intermittent_leave_periods[0]");
  }

  /**
   * Determine if claim is a Medical Leave claim
   * @returns {boolean}
   */
  get isMedicalLeave() {
    return get(this, "leave_details.reason") === LeaveReason.medical;
  }

  /**
   * Determine if claim is a reduced schedule leave claim
   * @returns {boolean}
   */
  get isReducedSchedule() {
    return !!get(this, "leave_details.reduced_schedule_leave_periods[0]");
  }

  /**
   * Check if Claim has been submitted yet. This affects the editability
   * of some fields, and as a result, the user experience.
   * @returns {boolean}
   */
  get isSubmitted() {
    return this.status === ClaimStatus.submitted;
  }

  /**
   * Returns full name accounting for any false values
   * @returns {string}
   */
  get fullName() {
    return compact([this.first_name, this.middle_name, this.last_name]).join(
      " "
    );
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
      work_pattern_days: undefined,
      work_pattern_type: null,
      work_week_starts: "Sunday",
    };
  }

  /**
   * Return work_pattern_days grouped by week_number.
   * @returns {Array.<WorkPatternDay[]>}
   */
  get weeks() {
    const workPatternDays = sortBy(
      [...get(this, "work_pattern_days", [])],
      (day) => OrderedDaysOfWeek.indexOf(day.day_of_week)
    );
    return Object.values(groupBy(workPatternDays, "week_number"));
  }

  /**
   * Return array with total minutes worked each week
   * @returns {number[]}
   */
  get minutesWorkedEachWeek() {
    return this.weeks.map((week) => {
      const hours = sumBy(week, "hours");
      const minutes = sumBy(week, "minutes");

      return 60 * hours + minutes;
    });
  }

  /**
   * Add a 7 day week to work_pattern_days.
   * @param {WorkPattern} workPattern - instance of a WorkPattern
   * @param {number} [minutesWorkedPerWeek] - average minutes worked per week. Must be an integer. If provided, will split hours evenly across 7 day week
   * @returns {WorkPattern}
   */
  static addWeek(workPattern, minutesWorkedPerWeek = 0) {
    const minutesOverWeek = WorkPattern._spreadMinutesOverWeek(
      minutesWorkedPerWeek
    );

    const newWeek = zip(OrderedDaysOfWeek, minutesOverWeek).map(
      ([day_of_week, minutes]) =>
        new WorkPatternDay({
          day_of_week,
          week_number: workPattern.weeks.length + 1,
          ...convertMinutesToHours(minutes),
        })
    );

    return new WorkPattern({
      ...workPattern,
      work_pattern_days: [
        ...get(workPattern, "work_pattern_days", []),
        ...newWeek,
      ],
    });
  }

  /**
   * Split provided minutes across a 7 day week
   * @param {number} minutesWorkedPerWeek - average hours worked per week. Must be an integer.
   * @returns {number[]}
   */
  static _spreadMinutesOverWeek(minutesWorkedPerWeek) {
    const remainder = minutesWorkedPerWeek % 7;
    return OrderedDaysOfWeek.map((day, i) => {
      if (i < remainder) {
        return Math.ceil(minutesWorkedPerWeek / 7);
      } else {
        return Math.floor(minutesWorkedPerWeek / 7);
      }
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
      hours: null,
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
      leave_period_id: null,
      start_date: null,
    };
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
  debit: "Debit",
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
