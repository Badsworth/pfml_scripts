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
      employer_fein: null,
      // TODO: This field does not yet exist in the API: https://lwd.atlassian.net/browse/CP-574
      employment_status: null,
      first_name: null,
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
    };
  }
}

/**
 * Enums for the Application's `leave_details.employment_status` field
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

export default Claim;
