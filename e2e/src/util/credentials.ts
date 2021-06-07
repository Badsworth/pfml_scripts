import { Credentials } from "../types";
import faker from "faker";
import config from "../config";

/**
 * Generates a random set of credentials.
 */
export function generateCredentials(): Credentials {
  const tag = faker.random.alphaNumeric(8);
  return {
    username: `${config("TESTMAIL_NAMESPACE")}.${tag}@inbox.testmail.app`,
    password: generatePassword(),
  };
}

function generatePassword(): string {
  // Password = {uppercase}{lowercase}{random*10){number}{symbol}
  return (
    faker.internet.password(1, false, /[A-Z]/) +
    faker.internet.password(1, false, /[a-z]/) +
    faker.internet.password(10) +
    faker.random.number(999) +
    faker.random.arrayElement(["@#$%^&*"])
  );
}

/**
 * Generates a reproducible set of credentials to use for a leave admin.
 *
 * The username is based on the FEIN, so this can't be used for a scenario where you want to generate
 * many different LAs for a single employer.
 */
export function getLeaveAdminCredentials(fein: string): Credentials {
  return {
    username: `${config("TESTMAIL_NAMESPACE")}.employer.${fein.replace(
      "-",
      ""
    )}@inbox.testmail.app`,
    password: config("EMPLOYER_PORTAL_PASSWORD"),
  };
}

/**
 * Fetches a reproducible set of credentials to use for logging in as a claimant.
 *
 * These credentials are used anytime we don't need a brand new claimant to submit with.
 */
export function getClaimantCredentials(): Credentials {
  return {
    username: config("PORTAL_USERNAME"),
    password: config("PORTAL_PASSWORD"),
  };
}
