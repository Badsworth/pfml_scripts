import { LeavePeriods } from "./types";
import { parseISO } from "date-fns";

export function extractLeavePeriod(
  claim: SimulationClaim["claim"],
  leaveType: keyof LeavePeriods = "continuous_leave_periods"
): [Date, Date] {
  const period = claim.leave_details?.[leaveType]?.[0];
  if (!period || !period.start_date || !period.end_date) {
    throw new Error("No leave period given");
  }
  return [parseISO(period.start_date), parseISO(period.end_date)];
}
