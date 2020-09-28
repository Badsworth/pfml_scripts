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
      fineos_absence_id: null,
      first_name: null,
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
        // TODO (CP-984): Connect to API
        has_continuous_leave_periods: null,
        // TODO (CP-567): this field doesn't exist in the API yet
        has_employer_benefits: null,
        // TODO (CP-1019): Connect address preference to the API
        has_mailing_address: null,
        // TODO (CP-567): this field doesn't exist in the API yet
        has_other_incomes: null,
        // TODO (CP-567): this field doesn't exist in the API yet
        has_previous_leaves: null,
        leave_details: {
          // TODO (CP-714): connect with reduced schedule periods fields to the API
          reduced_schedule_leave_periods: null,
        },
      },
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
    // TODO (CP-714): Remove once reduced schedule is integrated with API
    return (
      !!get(this, "temp.leave_details.reduced_schedule_leave_periods[0]") ||
      !!get(this, "leave_details.reduced_schedule_leave_periods[0]")
    );
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
 * Enums for an Application Document's `documentCategory` field
 * @enum {string}
 */
export const DocumentCategory = {
  active_duty_certification: "Active Duty Certification",
  bonding_certification: "Bonding Certification",
  identity_verification: "Identity Verification",
  medical_certification: "Medical Certification",
  notices: "Notices",
};

export default Claim;
