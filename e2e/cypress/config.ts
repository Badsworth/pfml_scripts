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
