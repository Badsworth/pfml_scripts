import LeaveReason from "../models/LeaveReason";
import { PreviousLeaveReason } from "../models/PreviousLeave";
import findKeyByValue from "./findKeyByValue";

/**
 * Converts a LeaveReason to its corresponding PreviousLeaveReason.
 * @param {string} leaveReason - the application leave reason
 * @returns {PreviousLeaveReason} the corresponding PreviousLeaveReason
 */
const leaveReasonToPreviousLeaveReason = (leaveReason) => {
  const previousLeaveReasonKey = findKeyByValue(LeaveReason, leaveReason);
  return PreviousLeaveReason[previousLeaveReasonKey];
};

export default leaveReasonToPreviousLeaveReason;
