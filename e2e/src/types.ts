import { ApplicationLeaveDetails } from "./api";

export type Credentials = {
  username: string;
  password: string;
  fein?: string;
};

export type OAuthCreds = {
  clientID: string;
  secretID: string;
};

export type LeavePeriods = Pick<
  ApplicationLeaveDetails,
  | "reduced_schedule_leave_periods"
  | "continuous_leave_periods"
  | "intermittent_leave_periods"
>;

export type notificationRequest = {
  notificationType: string;
  employeeName: string;
  recipientEmail: string;
};
export type Submission = {
  application_id: string;
  fineos_absence_id: string;
  timestamp_from: Date;
};
