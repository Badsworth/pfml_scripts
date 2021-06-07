import { PreviousLeave } from "../api";
import { getLeavePeriod } from "../util/claims";
import { ApplicationLeaveDetails } from "../_api";
import { ClaimSpecification } from "./Claim";

/**
 * Generates employer benefits for the claim. Prefills start & end dates to be the same as leave dates.
 * @param spec - Claim specification, if has other_incomes listed.
 */
export function generatePreviousLeaves(
  { previous_leaves }: ClaimSpecification,
  leave_details: ApplicationLeaveDetails
): PreviousLeave[] | undefined {
  if (!previous_leaves || !previous_leaves.length) return;

  const [startDate, endDate] = getLeavePeriod(leave_details);

  return previous_leaves.map((leave) => {
    // only set start and end dates if they weren't specified
    if (leave.leave_start_date) return leave;
    return {
      ...leave,
      leave_start_date: startDate,
      leave_end_date: endDate,
    };
  });
}
