import { ApplicationLeaveDetails } from "./api";
import * as scenarios from "./scenarios";
import {
  EmployerBenefit,
  PreviousLeave,
  ConcurrentLeave,
  OtherIncome,
} from "./_api";

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

export type Scenarios = keyof typeof scenarios;

/**
 * Require properties to be neither null nor undefined
 */
export type RequireNotNull<T, P extends keyof T> = AllNotNull<Pick<T, P>> &
  Pick<T, Exclude<keyof T, P>>;

/**
 * Exclude null and undefined from all of the properties of the given type T
 */
export type AllNotNull<T> = Required<
  {
    [P in keyof T]: NonNullable<T[P]>;
  }
>;

/**
 * @note Following types are used within typeguards and to limit the amount of property checks & type casts.
 */

/**
 * Has all the properties required to submit a previous leave.
 */
export type ValidPreviousLeave = Omit<
  AllNotNull<PreviousLeave>,
  "previous_leave_id"
>;

/**
 * Has all the properties required to submit a concurrent leave.
 */
export type ValidConcurrentLeave = Omit<
  AllNotNull<ConcurrentLeave>,
  "concurrent_leave_id"
>;

/**
 * Has all the properties required to submit an other income.
 */
export type ValidOtherIncome = Omit<AllNotNull<OtherIncome>, "other_income_id">;

/**
 * Has all the properties required to submit an employer benefit.
 */
export type ValidEmployerBenefit = Omit<
  AllNotNull<EmployerBenefit>,
  "employer_benefit_id"
>;
