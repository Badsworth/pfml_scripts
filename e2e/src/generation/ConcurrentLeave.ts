import { ConcurrentLeave } from "../api";
import { getLeavePeriod } from "../util/claims";
import { ApplicationLeaveDetails } from "../_api";
import { ClaimSpecification } from "./Claim";

/**
 * Generates concurrent leave for the claim. Prefills start & end dates to be the same as leave dates.
 * @param spec - Claim specification, will use the data given if has concurrent_leave listed.
 */
export function generateConcurrentLeaves(
  { concurrent_leave }: ClaimSpecification,
  leave_details: ApplicationLeaveDetails
): ConcurrentLeave | undefined {
  // if spec doesn't specify concurrent leave - return nothing
  if (!concurrent_leave) return;
  // if spec has a concurrent leave with both dates specified - let it pass through.
  if (concurrent_leave.leave_start_date && concurrent_leave.leave_end_date)
    return concurrent_leave;
  const [startDate, endDate] = getLeavePeriod(leave_details);
  // if spec has a concurrent leave with no dates specified - set dates to the claim leave dates.
  return {
    ...concurrent_leave,
    leave_start_date: startDate,
    leave_end_date: endDate,
  };
}
