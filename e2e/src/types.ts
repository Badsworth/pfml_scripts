import {
  ApplicationRequestBody,
  ApplicationLeaveDetails,
  PaymentPreferenceRequestBody,
} from "./api";

export type Credentials = {
  username: string;
  password: string;
  fein?: string;
};

export type OAuthCreds = {
  clientID: string;
  secretID: string;
};

/**
 * Special type to use to tell Typescript what properties `this` might contain on a Cypress
 * test step.
 *
 * Because we alias `credentials` and `application`, they can later be used by accessing `this.credentials`
 * and `this.application`, respectively.
 *
 * @see https://www.typescriptlang.org/docs/handbook/functions.html#this-parameters
 */
export type CypressStepThis = {
  credentials?: Credentials;
  employerUsername?: string;
  application?: ApplicationRequestBody;
  paymentPreference: PaymentPreferenceRequestBody;
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
