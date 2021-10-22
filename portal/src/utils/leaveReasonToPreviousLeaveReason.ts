import LeaveReason from "../models/LeaveReason";
import { PreviousLeaveReason } from "../models/PreviousLeave";
import findKeyByValue from "./findKeyByValue";

/**
 * Converts a LeaveReason to its corresponding PreviousLeaveReason.
 */
const leaveReasonToPreviousLeaveReason = (leaveReason: string) => {
  const previousLeaveReasonKey = findKeyByValue(LeaveReason, leaveReason);
  return PreviousLeaveReason[previousLeaveReasonKey];
};

export default leaveReasonToPreviousLeaveReason;
