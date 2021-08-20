import config from "../config";
import TestMailVerificationFetcher from "../submission/TestMailVerificationFetcher";
import AuthenticationManager from "../submission/AuthenticationManager";
import { CognitoUserPool } from "amazon-cognito-identity-js";
import PortalSubmitter from "../submission/PortalSubmitter";
import EmployerPool from "../generation/Employer";
import EmployeePool from "../generation/Employee";
import { ApplicationRequestBody } from "../_api";

/**
 * @file This file contains utility functions that are commonly shared.
 *
 * The most common thread between all of these utilities is that they use config() to create complex objects based on
 * specific configuration values. Utilities that do not fit this pattern should probably be in another file.
 */

export function getFineosBaseUrl(): string {
  const base = config("FINEOS_BASEURL");
  const username = config("FINEOS_USERNAME");
  const password = config("FINEOS_PASSWORD");
  const url = new URL(base);
  url.username = username;
  url.password = password;
  return url.toString();
}

export function getVerificationFetcher(): TestMailVerificationFetcher {
  return new TestMailVerificationFetcher(
    config("TESTMAIL_APIKEY"),
    config("TESTMAIL_NAMESPACE")
  );
}

export function getAuthManager(): AuthenticationManager {
  return new AuthenticationManager(
    new CognitoUserPool({
      UserPoolId: config("COGNITO_POOL"),
      ClientId: config("COGNITO_CLIENTID"),
    }),
    config("API_BASEURL"),
    getVerificationFetcher()
  );
}

export function getPortalSubmitter(): PortalSubmitter {
  return new PortalSubmitter(getAuthManager(), config("API_BASEURL"));
}

export function getEmployerPool(): Promise<EmployerPool> {
  return EmployerPool.load(config("EMPLOYERS_FILE"));
}

export function getEmployeePool(): Promise<EmployeePool> {
  return EmployeePool.load(config("EMPLOYEES_FILE"));
}

export function splitClaimToParts(
  claim: ApplicationRequestBody
): Partial<ApplicationRequestBody>[] {
  const { leave_details } = claim;
  return [
    {
      first_name: claim.first_name,
      middle_name: null,
      last_name: claim.last_name,
    },
    {
      has_mailing_address: claim.has_mailing_address,
      residential_address: claim.residential_address,
      mailing_address: claim.mailing_address,
    },
    {
      date_of_birth: claim.date_of_birth,
    },
    {
      has_state_id: claim.has_state_id,
      mass_id: claim.mass_id,
    },
    {
      tax_identifier: claim.tax_identifier,
    },
    {
      employment_status: claim.employment_status,
      employer_fein: claim.employer_fein,
    },
    {
      leave_details: {
        employer_notified: leave_details?.employer_notified,
        employer_notification_date: leave_details?.employer_notification_date,
      },
    },
    {
      work_pattern: {
        work_pattern_type: claim.work_pattern?.work_pattern_type,
      },
    },
    {
      hours_worked_per_week: claim.hours_worked_per_week,
      work_pattern: {
        work_pattern_days: claim.work_pattern?.work_pattern_days,
      },
    },
    {
      leave_details: {
        reason: leave_details?.reason,
        reason_qualifier: leave_details?.reason_qualifier,
      },
    },
    {
      leave_details: {
        child_birth_date: leave_details?.child_birth_date,
        child_placement_date: leave_details?.child_placement_date,
        pregnant_or_recent_birth: leave_details?.pregnant_or_recent_birth,
      },
    },
    {
      has_continuous_leave_periods: claim.has_continuous_leave_periods,
      leave_details: {
        continuous_leave_periods: leave_details?.continuous_leave_periods,
      },
    },
    {
      has_reduced_schedule_leave_periods:
        claim.has_reduced_schedule_leave_periods,
    },
    {
      has_intermittent_leave_periods: claim.has_intermittent_leave_periods,
    },
    {
      phone: {
        int_code: "1",
        phone_number: "844-781-3163",
        phone_type: "Cell",
      },
    },
    {
      has_previous_leaves_same_reason: claim.has_previous_leaves_same_reason,
    },
    {
      previous_leaves_same_reason: claim.previous_leaves_same_reason,
    },
    {
      has_previous_leaves_other_reason: claim.has_previous_leaves_other_reason,
    },
    {
      previous_leaves_other_reason: claim.previous_leaves_other_reason,
    },
    {
      has_concurrent_leave: claim.has_concurrent_leave,
    },
    {
      concurrent_leave: claim.concurrent_leave,
    },
    {
      has_employer_benefits: claim.has_employer_benefits,
    },
    {
      employer_benefits: claim.employer_benefits,
    },
    {
      has_other_incomes: claim.has_other_incomes,
    },
    {
      other_incomes: claim.other_incomes,
    },
  ];
}
