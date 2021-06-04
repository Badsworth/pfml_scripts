import { ApplicationLeaveDetails, ApplicationRequestBody } from "../_api";
import { isNotNull, LeavePeriods } from "../types";
import {
  max,
  addDays,
  parseISO,
  format,
  startOfWeek,
  addWeeks,
} from "date-fns";
import faker from "faker";

export function extractLeavePeriod(
  { leave_details }: ApplicationRequestBody,
  leaveType: keyof LeavePeriods = "continuous_leave_periods"
): [Date, Date] {
  if (isNotNull(leave_details)) {
    return getLeavePeriodFromLeaveDetails(leave_details, leaveType);
  } else throw new Error("Missing leave details");
}

/**
 * Converts an amount of minutes to hours + minutes, throws an error if the remainder of minutes is not a multiple of increment
 * @param totalMinutes
 * @param increment 15 by default
 * @returns hours and minutes as a tuple
 * @example <caption>With default increment of 15</caption>
 * minutesToHoursAndMinutes(225) => [3, 45]
 * @example <caption>With specified increment of 20</caption>
 * minutesToHoursAndMinutes(200, 20) => [3, 20]
 */
export function minutesToHoursAndMinutes(
  totalMinutes: number,
  increment = 15
): [number, number] {
  const hours = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;
  if (minutes % increment !== 0)
    throw new Error(`Amount of minutes is not a multiple of ${increment}`);
  return [hours, minutes];
}

export function dateToMMddyyyy(date: string): string {
  const dateObj = parseISO(date);
  return format(dateObj, "MM/dd/yyyy");
}

type DateRange = [Date, Date];
/**
 * Takes 2 date ranges in the form of a tuple [startDate, endDate]. Returns true if these ranges overlap, false otherwise.
 * @example
 * const range1 = [parseISO("01/01/1990"),parseISO("01/01/2010")]
 * const range2 = [parseISO("01/01/2000"),parseISO("01/01/2020")]
 * checkDateRangesIntersect(range1, range2) // true
 */
export function checkDateRangesIntersect(
  range1: DateRange,
  range2: DateRange
): boolean {
  const [startsEarlier, startsLater] =
    range1[0] <= range2[0] ? [range1, range2] : [range2, range1];
  if (startsLater[0] <= startsEarlier[1]) return true;
  return false;
}

export function getLeavePeriodFromLeaveDetails(
  leaveDetails: ApplicationLeaveDetails,
  leaveType: keyof LeavePeriods = "continuous_leave_periods"
): [Date, Date] {
  const period = leaveDetails[leaveType]?.[0];
  if (!period || !period.start_date || !period.end_date)
    throw new Error("No leave period given");

  return [parseISO(period.start_date), parseISO(period.end_date)];
}

export function getLeavePeriod(
  leave_details: ApplicationLeaveDetails
): [string, string] {
  let period;
  if (leave_details.continuous_leave_periods?.length)
    period = leave_details.continuous_leave_periods[0];
  if (leave_details.intermittent_leave_periods?.length)
    period = leave_details.intermittent_leave_periods[0];
  if (leave_details.reduced_schedule_leave_periods?.length)
    period = leave_details.reduced_schedule_leave_periods[0];
  if (period?.start_date && period.end_date) {
    return [period.start_date, period.end_date];
  } else {
    throw new Error("Claim missing leave periods");
  }
}
/**
 * Specific function for setting the start date past
 * July 1st, 2021 and within 60 days of submittal date.
 *
 * There's a Fineos restriction for caring leave claims
 * submitted before that date. Also returns end date
 * two weeks after start date (for proper payment calculation)
 *
 * @Reminder to remove once we're past 21 July, 20201
 */
export function getCaringLeaveStartEndDates(): [Date, Date] {
  const minStartDate = max([parseISO("2021-07-09"), new Date()]);
  const maxStartDate = addDays(new Date(), 60);
  const start = startOfWeek(faker.date.between(minStartDate, maxStartDate));
  const end = addWeeks(start, 2);
  return [start, end];
}
