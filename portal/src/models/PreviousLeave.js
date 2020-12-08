/* eslint sort-keys: ["error", "asc"] */
/**
 * @file Previous leave period
 */
import BaseModel from "./BaseModel";

class PreviousLeave extends BaseModel {
  get defaults() {
    return {
      id: null,
      is_for_current_employer: null,
      leave_end_date: null,
      leave_reason: null, // PreviousLeaveReason
      leave_start_date: null,
    };
  }
}

/**
 * Enums for the Application's `previous_leaves[].leave_reason` field
 * @enum {string}
 */
export const PreviousLeaveReason = {
  activeDutyFamily: "Military exigency family",
  bonding: "Child bonding",
  care: "Care for a family member",
  medical: "Serious health condition",
  pregnancy: "Pregnancy / Maternity",
  serviceMemberFamily: "Military caregiver",
  // Unknown may be displayed to Leave Admins, but isn't
  // an option we display to Claimants
  unknown: "Unknown",
};

export default PreviousLeave;
