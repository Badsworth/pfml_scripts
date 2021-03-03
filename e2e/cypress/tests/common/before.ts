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
 * Calling this function triggers a bail out if the test function fails.
 *
 * This is useful when you have a step that _must_ complete for the others to be successful, as it prevents us
 * from wasting time and producing confusing results if the initial step is unsuccessful.
 */
export function bailIfThisTestFails(): void {
  // Bail on the rest of the tests in this suite if this part fails.
  cy.on("fail", (err, runnable) => {
    runnable.parent?.bail(true);
    throw err;
  });
}

export function beforeFineos(): void {
  // Suppress known application errors in Fineos.
  cy.on("uncaught:exception", (e) => {
    if (
      e.message.match(
      /(#.(CaseOwnershipSummaryPanelElement|CaseParticipantsSummaryPanelElement)|panelsdrilldown)/
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

  // Set up a route we can listen to wait on ajax rendering to complete.
  cy.intercept(/ajax\/pagerender\.jsp/).as("ajaxRender");
}
