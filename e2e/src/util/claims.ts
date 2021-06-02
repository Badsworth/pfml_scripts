import { ApplicationRequestBody } from "../_api";
import { LeavePeriods } from "../types";
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
  claim: ApplicationRequestBody,
  leaveType: keyof LeavePeriods = "continuous_leave_periods"
): [Date, Date] {
  const period = claim.leave_details?.[leaveType]?.[0];
  if (!period || !period.start_date || !period.end_date) {
    throw new Error("No leave period given");
  }
  return [parseISO(period.start_date), parseISO(period.end_date)];
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

/**
 * Specific function for setting the start date past
 * July 21st, 2021 and within 60 days of submittal date.
 *
 * There's a Fineos restriction for caring leave claims
 * submitted before that date. Also returns end date
 * two weeks after start date (for proper payment calculation)
 *
 * @Reminder to remove once we're past 21 July, 20201
 */
export function getCaringLeaveStartEndDates(): [Date, Date] {
  const minStartDate = max([parseISO("2021-07-29"), new Date()]);
  const maxStartDate = addDays(new Date(), 60);
  const start = startOfWeek(faker.date.between(minStartDate, maxStartDate));
  const end = addWeeks(start, 2);
  return [start, end];
}
