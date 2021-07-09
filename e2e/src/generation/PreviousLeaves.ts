import { differenceInDays, formatISO, parseISO, subDays } from "date-fns";
import subWeeks from "date-fns/subWeeks";
import { PreviousLeave } from "../api";
import { getLeavePeriod } from "../util/claims";
import { ApplicationLeaveDetails } from "../_api";

/**
 * Generates previous leaves for the claim.
 * Prefills start & end dates such that previous leave will end 2 weeks before the start of the current leave.
 * @param spec - Previous leave specification.
 * @param leave_details - used to get the leave period for the current leave.
 */
export function generatePreviousLeaves(
  previous_leaves: PreviousLeave[] | undefined,
  leave_details: ApplicationLeaveDetails
): PreviousLeave[] | undefined {
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

  return previous_leaves
    ? previous_leaves.map(setLeaveDatesIfNotSpecified)
    : undefined;
}
