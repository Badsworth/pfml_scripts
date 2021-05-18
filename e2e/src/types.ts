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
  | "request for additional info";
