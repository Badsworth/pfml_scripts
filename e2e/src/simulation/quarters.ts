import { endOfQuarter, subQuarters } from "date-fns";

export function parseOrPassISODate(candidate: string | Date): Date {
  if (candidate instanceof Date) {
    return candidate;
  }
  return parseISODateAsLocal(candidate);
}

/**
 * Parses an ISO date string, creating a Date object adjusted for the local time.
 *
 * This works around the problem where a date-only string will be parsed as UTC.
 * This should be used anywhere we parse a date-only string and use regular (non-UTC)
 * formatting functions.
 *
 * @param str
 */
export function parseISODateAsLocal(str: string): Date {
  const utc = new Date(str);
  return new Date(utc.getTime() + utc.getTimezoneOffset() * 1000 * 60);
}

const now = new Date();

// Return the end of the last N quarters from a reference date.
export default function quarters(refDate = now, number = 4): Date[] {
  const quarters = [];

  for (let i = number; i > 0; i--) {
    quarters.push(endOfQuarter(subQuarters(refDate, i)));
  }
  return quarters;
}
