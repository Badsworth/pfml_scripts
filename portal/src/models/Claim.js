/* eslint sort-keys: ["error", "asc"] */
/**
 * @file Benefits application model and enum values
 */
import BaseModel from "./BaseModel";

class Claim extends BaseModel {
  get defaults() {
    return {
      application_id: null,
      // TODO: We'll map this to the correct API field once we get into Intermittent Leave work
      avg_weekly_hours_worked: null,
      created_at: null,
      duration_type: null,
      employee_ssn: null,
      employer_benefits: [],
      employer_fein: null,
      // TODO: This field does not yet exist in the API: https://lwd.atlassian.net/browse/CP-574
      employment_status: null,
      first_name: null,
      // TODO: this field doesn't exist in the API yet: https://lwd.atlassian.net/browse/CP-567
      has_employer_benefits: null,
      // TODO: this field doesn't exist in the API yet: https://lwd.atlassian.net/browse/CP-567
      has_other_incomes: null,
      // TODO: this field doesn't exist in the API yet: https://lwd.atlassian.net/browse/CP-567
      has_previous_leaves: null,
      // TODO: We'll map this to the correct API field once we get into Intermittent Leave work
      hours_off_needed: null,
      last_name: null,
      leave_details: {
        continuous_leave_periods: null,
        employer_notification_date: null,
        employer_notified: null,
        reason: null,
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
        // TODO: Connect payment preference entry fields to the API: https://lwd.atlassian.net/browse/CP-703
        payment_preferences: [], // See the PaymentPreference class
      },
    };
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
  employed: "employed",
  selfEmployed: "self-employed",
  unemployed: "unemployed",
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

/**
 * Model for entries in the Application's `payment_preferences` array field
 * TODO: Map these to new API fields https://lwd.atlassian.net/browse/CP-703
 */
export class PaymentPreference extends BaseModel {
  get defaults() {
    return {
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
