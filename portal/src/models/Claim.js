/* eslint sort-keys: ["error", "asc"] */
/**
 * @file Benefits application model and enum values
 */
import BaseModel from "./BaseModel";
import { get } from "lodash";

class Claim extends BaseModel {
  get defaults() {
    return {
      application_id: null,
      created_at: null,
      employee_ssn: null,
      employer_benefits: [],
      employer_fein: null,
      employment_status: null,
      first_name: null,
      // TODO: this field doesn't exist in the API yet: https://lwd.atlassian.net/browse/CP-567
      has_employer_benefits: null,
      // TODO: this field doesn't exist in the API yet: https://lwd.atlassian.net/browse/CP-567
      has_other_incomes: null,
      // TODO: this field doesn't exist in the API yet: https://lwd.atlassian.net/browse/CP-567
      has_previous_leaves: null,
      last_name: null,
      leave_details: {
        continuous_leave_periods: [],
        employer_notification_date: null,
        employer_notified: null,
        intermittent_leave_periods: [],
        reason: null,
        reduced_schedule_leave_periods: [],
      },
      middle_name: null,
      other_incomes: [],
      pregnant_or_recent_birth: null,
      previous_leaves: [],
      status: null,
      /**
       * Fields within the `temp` object haven't been connected to the API yet, and
       * should have a ticket in Jira related to eventually moving them out of
       * this temporary space.
       */
      temp: {
        leave_details: {
          // TODO (CP-719): Connect intermittent leave fields to the API
          avg_weekly_work_hours: null,
          // TODO: connect with continuous schedule periods fields to the API: https://lwd.atlassian.net/browse/CP-720
          continuous_leave_periods: [],
          // TODO (CP-724): Connect start and end date to API
          end_date: null,
          // TODO: connect with reduced schedule periods fields to the API: https://lwd.atlassian.net/browse/CP-714
          reduced_schedule_leave_periods: [],
          // TODO (CP-724): Connect start and end date to API
          start_date: null,
        },
        // TODO: Connect payment preference entry fields to the API: https://lwd.atlassian.net/browse/CP-703
        payment_preferences: [
          {
            // Fields for ACH details
            account_details: {
              account_number: null,
              routing_number: null,
            },
            // Fields for where to send the debit card
            destination_address: {
              city: null,
              line_1: null,
              line_2: null,
              state: null,
              zip: null,
            },
            payment_method: null, // PaymentPreferenceMethod
            payment_preference_id: null,
          },
        ],
      },
    };
  }

  /**
   * Determine if claim is a continuous leave claim
   * @returns {boolean}
   */
  get isContinuous() {
    return !!get(this, "temp.leave_details.continuous_leave_periods[0]");
  }

  /**
   * Determine if claim is an intermittent leave claim
   * @returns {boolean}
   */
  get isIntermittent() {
    return !!get(this, "leave_details.intermittent_leave_periods[0]");
  }

  /**
   * Determine if claim is a reduced schedule leave claim
   * @returns {boolean}
   */
  get isReducedSchedule() {
    return !!get(this, "temp.leave_details.reduced_schedule_leave_periods[0]");
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
  // TODO: We need to map some of these to the correct API fields,
  // once those enum values exist within the API
  // https://lwd.atlassian.net/browse/CP-515
  activeDutyFamily: "Care For A Family Member",
  bonding: "Child Bonding",
  medical: "Serious Health Condition - Employee",
  serviceMemberFamily: "Pregnancy/Maternity",
};

export class ContinuousLeavePeriod extends BaseModel {
  get defaults() {
    return {
      weeks: null,
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
      // Estimate how many absences {per week|per month|over the next 6 months}
      frequency: null,
      // Implied by input selection of "over the next 6 months"
      // and can only ever be equal to 6
      frequency_interval: null,
      // How often might you need to be absent from work?
      frequency_interval_basis: null,
    };
  }
}

/**
 * Enums for the Application's `intermittent_leave_periods[].frequency_interval_basis` field
 * @enum {string}
 */
export const FrequencyIntervalBasis = {
  days: "Days",
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
  minutes: "Minutes",
};

export class ReducedScheduleLeavePeriod extends BaseModel {
  get defaults() {
    return {
      hours_per_week: null,
      weeks: null,
    };
  }
}

/**
 * Enums for the Application's `payment_preferences[].payment_method` field
 * @enum {string}
 */
export const PaymentPreferenceMethod = {
  ach: "ACH",
  // TODO: Map to a valid enum for debit https://lwd.atlassian.net/browse/CP-703
  debit: "Debit",
};

export default Claim;
