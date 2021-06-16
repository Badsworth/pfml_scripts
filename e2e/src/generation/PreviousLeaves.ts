import { differenceInDays, formatISO, parseISO, subDays } from "date-fns";
import subWeeks from "date-fns/subWeeks";
import { PreviousLeave } from "../api";
import { NonEmptyArray } from "../types";
import { getLeavePeriod } from "../util/claims";
import { ApplicationLeaveDetails } from "../_api";
import { ClaimSpecification } from "./Claim";

/**
 * Generates previous leaves for the claim.
 * Prefills start & end dates such that previous leave will end 2 weeks before the start of the current leave.
 * @param spec - Claim specification.
 * @param leave_details - used to get the leave period for the current leave.
 */
export function generatePreviousLeaves(
  {
    previous_leaves_same_reason,
    previous_leaves_other_reason,
  }: ClaimSpecification,
  leave_details: ApplicationLeaveDetails
): Pick<
  ClaimSpecification,
  "previous_leaves_other_reason" | "previous_leaves_same_reason"
> {
  const [startDate, endDate] = getLeavePeriod(leave_details);

  const setLeaveDatesIfNotSpecified = (leave: PreviousLeave) => {
    if (leave.leave_start_date && leave.leave_end_date) {
      if (parseISO(leave.leave_start_date) < parseISO(leave.leave_end_date))
        return leave;
      throw new Error(
        `Leave end date (${leave.leave_end_date}) cannot be before leave start date (${leave.leave_start_date})`
      );
    }
    // previous leave ends 2 weeks before the start of the current leave
    const leave_end_date = formatISO(subWeeks(parseISO(startDate), 2), {
      representation: "date",
    });
    // Is of the same length as current leave.
    const leave_start_date = formatISO(
      subDays(
        parseISO(leave_end_date),
        differenceInDays(parseISO(endDate), parseISO(startDate))
      ),
      {
        representation: "date",
      }
    );
    return {
      ...leave,
      leave_start_date,
      leave_end_date,
    };
  };

  previous_leaves_same_reason = previous_leaves_same_reason
    ? (previous_leaves_same_reason.map(
        setLeaveDatesIfNotSpecified
      ) as NonEmptyArray<PreviousLeave>)
    : undefined;
  previous_leaves_other_reason = previous_leaves_other_reason
    ? (previous_leaves_other_reason.map(
        setLeaveDatesIfNotSpecified
      ) as NonEmptyArray<PreviousLeave>)
    : undefined;

  return { previous_leaves_other_reason, previous_leaves_same_reason };
}
