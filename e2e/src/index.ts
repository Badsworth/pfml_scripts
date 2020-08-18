/**
 * Returns a URL for Fineos with embedded username and password.
 */
export function getFineosBaseUrl(): string {
  const base = Cypress.env("FINEOS_BASEURL");
  const username = Cypress.env("FINEOS_USERNAME");
  const password = Cypress.env("FINEOS_PASSWORD");
  if (!base)
    throw new Error(
      `You must set the CYPRESS_FINEOS_BASEURL environment variable.`
    );
  if (!username)
    throw new Error(
      `You must set the CYPRESS_FINEOS_USERNAME environment variable.`
    );
  if (!password)
    throw new Error(
      `You must set the CYPRESS_FINEOS_PASSWORD environment variable.`
    );
  const url = new URL(base);
  url.username = username;
  url.password = password;
  return url.toString();
}

export function setFeatureFlags(): void {
  cy.setCookie(
    "_ff",
    JSON.stringify({
      pfmlTerriyay: true,
    })
  );
}

export function catchStatusError(): void {
  cy.on("uncaught:exception", (e) => {
    // Suppress failures due to this error, which we can't do anything about.
    if (e.message.indexOf(`Cannot set property 'status' of undefined`)) {
      return false;
    }
  });
}
