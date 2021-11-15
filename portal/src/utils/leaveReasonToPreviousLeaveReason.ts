import LeaveReason from "../models/LeaveReason";
import { PreviousLeaveReason } from "../models/PreviousLeave";
import findKeyByValue from "./findKeyByValue";

/**
 * Converts a LeaveReason to its corresponding PreviousLeaveReason.
 */
const leaveReasonToPreviousLeaveReason = (leaveReason: string | null) => {
  const previousLeaveReasonKey = findKeyByValue(LeaveReason, leaveReason);
  return previousLeaveReasonKey
    ? PreviousLeaveReason[previousLeaveReasonKey]
    : undefined;
};

export default leaveReasonToPreviousLeaveReason;
