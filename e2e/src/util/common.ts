import config from "../config";
import TestMailVerificationFetcher from "../submission/TestMailVerificationFetcher";
import AuthenticationManager from "../submission/AuthenticationManager";
import { CognitoUserPool } from "amazon-cognito-identity-js";
import PortalSubmitter from "../submission/PortalSubmitter";
import EmployerPool from "../generation/Employer";
import EmployeePool from "../generation/Employee";

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
