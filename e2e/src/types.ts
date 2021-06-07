import { ApplicationLeaveDetails } from "./api";

export type Credentials = {
  username: string;
  password: string;
};

export type OAuthCreds = {
  clientID: string;
  secretID: string;
};

export type LeaveReason = NonNullable<ApplicationLeaveDetails["reason"]>;

export type LeavePeriods = Pick<
  ApplicationLeaveDetails,
  | "reduced_schedule_leave_periods"
  | "continuous_leave_periods"
  | "intermittent_leave_periods"
>;

export type Submission = {
  application_id: string;
  fineos_absence_id: string;
  timestamp_from: number;
};

export type SubjectOptions =
  | "application started"
  | "employer response"
  | "denial (employer)"
  | "approval (employer)"
  | "denial (claimant)"
  | "approval (claimant)"
  | "review leave hours"
  | "request for additional info";

// Type utils

/**
 * Check whether a given value is neither null nor undefined.
 * @param arg - value to check
 * @example
 * isNotNull(null) => false
 * isNotNull("") => true
 */
export function isNotNull<T>(arg: T): arg is NonNullable<T> {
  return arg !== null && arg !== undefined;
}

/**
 * Check whether a given value is an array where
 * each member is of a specified type
 *
 * @param arr - array to check
 * @param check - type guard to use when evaluating each item
 * @example
 * isTypedArray(["", false, true], isNotNull) => true
 */
export function isTypedArray<T>(
  arr: unknown,
  check: (x: unknown) => x is T
): arr is T[] {
  if (!Array.isArray(arr)) return false;
  if (arr.some((item) => !check(item))) return false;
  return true;
}
