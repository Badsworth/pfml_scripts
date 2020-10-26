import { ApplicationRequestBody, ApplicationLeaveDetails } from "./api";

export type Credentials = {
  username: string;
  password: string;
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
  application?: ApplicationRequestBody;
};

export type LeavePeriods = Pick<
  ApplicationLeaveDetails,
  | "reduced_schedule_leave_periods"
  | "continuous_leave_periods"
  | "intermittent_leave_periods"
>;

// Used for Cucumber parameters.
export const ScenarioClaimTestTypes = [
  "HAP1",
  "HAP2",
  "HAP3",
  "MHAP4",
  "MHAP5",
  "GBR1",
  "UNH2",
  "UNH3",
  "GBM1",
] as const;
export type TestType = typeof ScenarioClaimTestTypes[number];
