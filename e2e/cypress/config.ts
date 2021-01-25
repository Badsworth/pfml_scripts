import type { Credentials } from "../src/types";

/**
 * Returns a URL for Fineos with embedded username and password.
 */
export function getFineosBaseUrl(): string {
  const base = Cypress.env("E2E_FINEOS_BASEURL");
  const username = Cypress.env("E2E_FINEOS_USERNAME");
  const password = Cypress.env("E2E_FINEOS_PASSWORD");
  if (!base)
    throw new Error(
      `You must set the E2E_FINEOS_BASEURL environment variable.`
    );
  if (!username)
    throw new Error(
      `You must set the E2E_FINEOS_USERNAME environment variable.`
    );
  if (!password)
    throw new Error(
      `You must set the E2E_FINEOS_PASSWORD environment variable.`
    );
  const url = new URL(base);
  url.username = username;
  url.password = password;
  return url.toString();
}

export function getLeaveAdminCredentials(fein: string): Credentials {
  // Backward compatibility - throw error if the employer is not one of our "blessed" employers.
  if (!["84-7847847", "99-9999999"].includes(fein)) {
    throw new Error(`Unable to determine Leave Admin credentials for ${fein}`);
  }
  const password = Cypress.env("E2E_EMPLOYER_PORTAL_PASSWORD");
  if (!password) {
    throw new Error(
      `You must set the E2E_EMPLOYER_PORTAL_PASSWORD environment variable.`
    );
  }
  return {
    username: `gqzap.employer.${fein.replace("-", "")}@inbox.testmail.app`,
    password,
  };
}
