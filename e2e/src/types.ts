import { ApplicationLeaveDetails, ApplicationRequestBody } from "./api";
import * as scenarios from "./scenarios";
import {
  EmployerBenefit,
  PreviousLeave,
  ConcurrentLeave,
  OtherIncome,
} from "./_api";
import { DehydratedClaim } from "./generation/Claim";

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
  | "request for additional info"
  | "extension of benefits";

export type Scenarios = keyof typeof scenarios;

export type PersonalIdentificationDetails = {
  id_number_type: "Social Security Number" | "ID" | "ITIN";
  date_of_birth: string;
  gender: NonNullable<ApplicationRequestBody["gender"]>;
  marital_status:
    | "Unknown"
    | "Single"
    | "Married"
    | "Divorced"
    | "Widowed"
    | "Separated";
};

/**
 * @note UTILITY TYPES
 */

/**
 * Require properties in P to be neither null nor undefined within T
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

/**Get a union of non-optional keys of type */
export type RequiredKeys<T> = {
  [k in keyof T]-?: undefined extends T[k] ? never : k;
}[keyof T];

/**
 * Require a typed array to have at least one element.
 */
export type NonEmptyArray<T> = [T, ...T[]];

/**
 * @note Following types are used within typeguards and to limit the amount of property checks & type casts.
 */

/**
 * Has all the properties required to submit a previous leave.
 */
export type ValidPreviousLeave = RequireNotNull<
  PreviousLeave,
  Exclude<keyof PreviousLeave, "previous_leave_id">
>;

/**
 * Has all the properties required to submit a concurrent leave.
 */
export type ValidConcurrentLeave = RequireNotNull<
  ConcurrentLeave,
  Exclude<keyof ConcurrentLeave, "concurrent_leave_id">
>;

/**
 * Has all the properties required to submit an other income.
 */
export type ValidOtherIncome = RequireNotNull<
  OtherIncome,
  Exclude<keyof OtherIncome, "other_income_id">
>;

/**
 * Has all the properties required to submit an employer benefit.
 */
export type ValidEmployerBenefit = RequireNotNull<
  EmployerBenefit,
  Exclude<keyof EmployerBenefit, "employer_benefit_id">
>;

/**
 * Used to assert the existence of following properties on a generated claim.
 */
export type ValidClaim = RequireNotNull<
  DehydratedClaim["claim"],
  | "first_name"
  | "last_name"
  | "tax_identifier"
  | "employer_fein"
  | "date_of_birth"
  | "leave_details"
>;
