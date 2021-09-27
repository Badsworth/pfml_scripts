/**
 * @file Wrapper methods around our monitoring service. Methods in here should
 * handle a scenario where the monitoring service is blocked by things like an ad blocker.
 */

/**
 * Module level global variable keeping track of custom attributes that should be added to all events within a single page,
 * including errors, events, and browser interactions.
 * @type {object.<string, string|number>}
 */
const moduleGlobal = {
  customPageAttributes: {},
};

/**
 * Configure our monitoring services with environment-specific key/ids
 */
function initialize() {
  // Don't break when rendered in a non-browser environment
  if (typeof window === "undefined") return;

  // NREUM = New Relic
  window.NREUM = window.NREUM || {};
  window.NREUM.loader_config = {
    agentID: `${process.env.newRelicAppId}`,
    applicationID: `${process.env.newRelicAppId}`,
    accountID: "2837112",
    trustKey: "1606654",
    licenseKey: "NRJS-9852fe81d192bbc09c5",
  };
  window.NREUM.info = {
    applicationID: `${process.env.newRelicAppId}`,
    beacon: "bam.nr-data.net",
    errorBeacon: "bam.nr-data.net",
    licenseKey: "NRJS-9852fe81d192bbc09c5",
    sa: 1,
  };
}

/**
 * Check if New Relic is loaded and ready for its API methods to be called.
 * `newrelic` is exposed as a global variable when the New Relic JS snippet
 * is loaded. See docs/portal/monitoring.md for details.
 * @returns {boolean}
 */
function newrelicReady() {
  return typeof newrelic !== "undefined";
}

/**
 * Track a JS error
 * @see https://docs.newrelic.com/docs/browser/new-relic-browser/browser-agent-spa-api/noticeerror-browser-agent-api
 * @param {Error} error
 * @param {object} [customAttributes] - name/value pairs representing custom attributes
 */
function noticeError(error, customAttributes) {
  if (newrelicReady()) {
    newrelic.noticeError(error, {
      ...moduleGlobal.customPageAttributes,
      ...customAttributes,
      environment: process.env.buildEnv,
      portalReleaseVersion: process.env.releaseVersion,
    });
  }
}

/**
 * Track Single Page App (SPA) route changes in New Relic and give them more accurate names.
 * @see https://docs.newrelic.com/docs/browser/new-relic-browser/guides/guide-using-browser-spa-apis
 * @see https://docs.newrelic.com/docs/browser/new-relic-browser/browser-agent-spa-api/spa-set-current-route-name
 * @param {string} routeName Route names should represent a routing pattern
 * @param {object.<string, string|number>} [customPageAttributes] Optional custom attributes to set for the page and for subsequent events on the same page
 *  rather than a specific resource. For example /claims/:id rather than /claims/123
 */
function startPageView(routeName, customPageAttributes) {
  if (newrelicReady()) {
    // First end previous interaction if that's still in progress
    newrelic.interaction().end();

    moduleGlobal.customPageAttributes = customPageAttributes || {};
    newrelic.interaction();
    setPageAttributesOnInteraction();
    newrelic.setCurrentRouteName(routeName);
  }
}

/**
 * Track a page action or event
 * @see https://docs.newrelic.com/docs/browser/new-relic-browser/browser-agent-spa-api/add-page-action
 * @param {string} name - Name or category of the action
 * @param {object} [customAttributes] - name/value pairs representing custom attributes
 */
function trackEvent(name, customAttributes) {
  if (newrelicReady()) {
    newrelic.addPageAction(name, {
      ...moduleGlobal.customPageAttributes,
      ...customAttributes,
      environment: process.env.buildEnv,
      portalReleaseVersion: process.env.releaseVersion,
    });
  }
}

/**
 * For New Relic, Fetch requests are only recorded if they are executed during a BrowserInteraction event,
 * which by default happens during the initial page load and any time the route is changed. That means
 * for other cases, we need to manually initiate a BrowserInteraction so the request is tracked.
 * @see https://docs.newrelic.com/docs/browser/new-relic-browser/troubleshooting/troubleshoot-ajax-data-collection
 * @param {string} requestName - URL being fetched (if known) or name representing the request
 * @example trackFetchRequest('https://paidleave-api.mass.gov/applications'); request(...);
 */
function trackFetchRequest(requestName) {
  if (newrelicReady()) {
    // First end previous interaction if that's still in progress
    newrelic.interaction().end();

    const trackedName = requestName.replace("https://", "");
    newrelic.interaction().setName(`fetch: ${trackedName}`);
    newrelic.interaction().setAttribute("environment", process.env.buildEnv);
    newrelic
      .interaction()
      .setAttribute("portalReleaseVersion", process.env.releaseVersion);
    setPageAttributesOnInteraction();
    newrelic.interaction().save();
  }
}

/**
 * Call this after a fetch request being tracked with trackFetchRequest has completed,
 * so subsequent requests made by third-party scripts (e.g Google Analytics) don't get
 * tracked under the same browser interaction.
 */
function markFetchRequestEnd() {
  if (newrelicReady()) {
    newrelic.interaction().end();
  }
}

/**
 * @private
 */
function setPageAttributesOnInteraction() {
  if (newrelicReady()) {
    for (const [name, value] of Object.entries(
      moduleGlobal.customPageAttributes
    )) {
      newrelic.interaction().setAttribute(name, value);
    }
  }
}

export default {
  initialize,
  markFetchRequestEnd,
  noticeError,
  startPageView,
  trackEvent,
  trackFetchRequest,
};
