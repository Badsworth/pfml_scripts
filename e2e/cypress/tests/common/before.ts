export function beforePortal(): void {
  // Set the feature flag necessary to see the portal.
  cy.setCookie(
    "_ff",
    JSON.stringify({
      pfmlTerriyay: true,
      claimantShowAuth: true,
      claimantShowMedicalLeaveType: true,
      noMaintenance: true,
      employerShowSelfRegistrationForm: true,
      claimantShowOtherLeaveStep: true,
      claimantAuthThroughApi: true,
      employerShowAddOrganization: true,
      employerShowVerifications: true,
    }),
    { log: true }
  );

  cy.on("uncaught:exception", (e) => {
    if (e.message.match(/Cannot set property 'status' of undefined/)) {
      return false;
    }
    return true;
  });

  // Setup a route for application submission so we can extract claim ID later.
  cy.intercept({
    method: "POST",
    url: "**/api/v1/applications/*/submit_application",
  }).as("submitClaimResponse");

  // Block new-relic.js outright due to issues with Cypress networking code.
  // Without this block, test retries on the portal error out due to fetch() errors.
  cy.intercept("**/new-relic.js", (req) => {
    req.reply("console.log('Fake New Relic script loaded');");
  });
}

/**
 * This function is used to fetch and set the proper cookies for access Fineos UAT
 *
 * Note: Only used for UAT enviornment
 */
function SSO(): void {
  cy.clearCookies();
  // Perform SSO login in a task. We can't visit other domains in Cypress.
  cy.task("completeSSOLoginFineos").then((cookiesJson) => {
    const deserializedCookies: Record<string, string>[] = JSON.parse(
      cookiesJson
    );
    // There's no way we can stop the redirection from Fineos -> SSO login.
    // What we _can_ do is set the login cookies so that when that request is made,
    // it bounces back immediately with a HTTP redirect instead of showing the login page.
    const noSecure = deserializedCookies.filter((cookie) =>
      cookie.domain.match(/login\.microsoftonline/)
    );
    for (const cookie_info of noSecure) {
      cy.setCookie(cookie_info.name, cookie_info.value, cookie_info);
    }
  });
}

export function beforeFineos(): void {
  // Suppress known application errors in Fineos.
  cy.on("uncaught:exception", (e) => {
    if (
      e.message.match(
        /(#.(CaseOwnershipSummaryPanelElement|CaseParticipantsSummaryPanelElement)|panelsdrilldown|startHeartbeatMonitorForPage)/
      )
    ) {
      return false;
    }
    if (e.message.match(/Cannot set property 'status' of undefined/)) {
      return false;
    }
    return true;
  });
  // Block new-relic.js outright due to issues with Cypress networking code.
  // Without this block, test retries on the portal error out due to fetch() errors.
  cy.intercept("https://js-agent.newrelic.com/*", (req) => {
    req.reply("console.log('Fake New Relic script loaded');");
  });

  // Fineos error pages have been found to cause test crashes when rendered. This is very hard to debug, as Cypress
  // crashes with no warning and removes the entire run history, so when a Fineos error page is detected, we instead
  // throw an error.
  cy.intercept(/\/util\/errorpage.jsp/, (req) => {
    req.reply(
      "A fatal Fineos error was thrown at this point. We've blocked the rendering of this page to prevent test crashes"
    );
  });

  // Set up a route we can listen to wait on ajax rendering to complete.
  cy.intercept(/ajax\/pagerender\.jsp/).as("ajaxRender");

  if (Cypress.env("E2E_ENVIRONMENT") === "uat") {
    SSO();
  }
}
