/* eslint sort-keys: ["error", "asc"] */
/**
 * @file Previous leave period
 */
import { ValuesOf } from "../../types/common";

class PreviousLeave {
  is_for_current_employer: boolean | null = null;
  leave_end_date: string | null = null;
  leave_minutes: number | null = null;
  leave_reason: ValuesOf<typeof PreviousLeaveReason> | null = null;

  leave_start_date: string | null = null;
  previous_leave_id: string | null = null; // currently only used by the /applications API in the Claimant portal.
  type: ValuesOf<typeof PreviousLeaveType> | null = null;
  worked_per_week_minutes: number | null = null;

  constructor(attrs: Partial<PreviousLeave>) {
    Object.assign(this, attrs);
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
} as const;

/**
 * Possible values for Application's "previous_leaves[].type" field.
 * @enum {string}
 */
export const PreviousLeaveType = {
  otherReason: "other_reason",
  sameReason: "same_reason",
} as const;

export default PreviousLeave;
