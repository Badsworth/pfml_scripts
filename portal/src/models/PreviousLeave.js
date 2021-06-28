/* eslint sort-keys: ["error", "asc"] */
/**
 * @file Previous leave period
 */
import BaseModel from "./BaseModel";

class PreviousLeave extends BaseModel {
  get defaults() {
    return {
      is_for_current_employer: null,
      is_for_same_reason_as_leave_reason: null,
      leave_end_date: null,
      leave_minutes: null,
      leave_reason: null, // PreviousLeaveReason
      leave_start_date: null,
      // this ID field is currently only used by the /applications API in the Claimant portal.
      previous_leave_id: null,
      worked_per_week_minutes: null,
    };
  }
}

/**
 * Enums for the Application's `previous_leaves[].leave_reason` field
 * @enum {string}
 */
export const PreviousLeaveReason = {
  activeDutyFamily:
    "Managing family affairs while a family member is on active duty in the armed forces",
  bonding: "Bonding with my child after birth or placement",
  care: "Caring for a family member with a serious health condition",
  medical: "An illness or injury",
  pregnancy: "Pregnancy",
  serviceMemberFamily:
    "Caring for a family member who serves in the armed forces",
  // Unknown may be displayed to Leave Admins, but isn't
  // an option we display to Claimants
  unknown: "Unknown",
};

export default PreviousLeave;
