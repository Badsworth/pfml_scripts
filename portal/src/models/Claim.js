/* eslint sort-keys: ["error", "asc"] */
/**
 * @file Benefits application model and enum values
 */
import Address from "./Address";
import BaseModel from "./BaseModel";
import { get } from "lodash";

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
      first_name: null,
      // TODO (CP-567): this field doesn't exist in the API yet
      has_employer_benefits: null,
      // TODO (CP-567): this field doesn't exist in the API yet
      has_other_incomes: null,
      // TODO (CP-567): this field doesn't exist in the API yet
      has_previous_leaves: null,
      has_state_id: null,
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
      mass_id: null,
      middle_name: null,
      // array of OtherIncome objects. See the OtherIncome model
      other_incomes: [],
      // array of PreviousLeave objects. See the PreviousLeave model
      previous_leaves: [],
      status: null,
      tax_identifier: null,
      /**
       * Fields within the `temp` object haven't been connected to the API yet, and
       * should have a ticket in Jira related to eventually moving them out of
       * this temporary space.
       */
      temp: {
        leave_details: {
          // TODO (CP-719): Connect intermittent leave fields to the API
          avg_weekly_work_hours: null,
          // TODO (CP-720): connect with continuous schedule periods fields to the API
          continuous_leave_periods: null,
          // TODO (CP-724): Connect start and end date to API
          end_date: null,
          // TODO (CP-714): connect with reduced schedule periods fields to the API
          reduced_schedule_leave_periods: null,
          // TODO (CP-724): Connect start and end date to API
          start_date: null,
        },
        // TODO (CP-703): Connect payment preference entry fields to the API
        payment_preferences: [
          {
            // Fields for ACH details
            account_details: {
              account_number: null,
              routing_number: null,
            },
            // Fields for where to send the debit card
            destination_address: new Address(),
            payment_method: null, // PaymentPreferenceMethod
            payment_preference_id: null,
          },
        ],
        // TODO (CP-841): Connect address to API
        residential_address: new Address(),
      },
    };
  }

  /**
   * Determine if claim is a continuous leave claim
   * @returns {boolean}
   */
  get isContinuous() {
    // TODO (CP-720): Remove once continuous leave is integrated with API
    return (
      !!get(this, "temp.leave_details.continuous_leave_periods[0]") ||
      !!get(this, "leave_details.continuous_leave_periods[0]")
    );
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
    // TODO (CP-714): Remove once reduced schedule is integrated with API
    return (
      !!get(this, "temp.leave_details.reduced_schedule_leave_periods[0]") ||
      !!get(this, "leave_details.reduced_schedule_leave_periods[0]")
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
  // TODO (CP-515): We need to map some of these to the correct API fields,
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
      leave_period_id: null,
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
      leave_period_id: null,
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
      leave_period_id: null,
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
  // TODO (CP-703): Map to a valid enum for debit
  debit: "Debit",
};

export default Claim;
