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
  activeDutyFamily: "Military Exigency Family",
  bonding: "Child Bonding",
  care: "Care For A Family Member",
  medical: "Serious Health Condition - Employee",
  pregnancy: "Pregnancy/Maternity",
  serviceMemberFamily: "Military Caregiver",
};

export default PreviousLeave;
