/**
 * @file Wrapper methods around our monitoring service. Methods in here should
 * handle a scenario where the monitoring service is blocked by things like an ad blocker.
 */
import type NewRelicBrowser from "new-relic-browser";

export interface NewRelicEventAttributes {
  [name: string]: number | string;
}

declare global {
  interface Window {
    NREUM?: { [key: string]: unknown };
    newrelic?: typeof NewRelicBrowser;
  }
}

/**
 * Module level global variable keeping track of custom attributes that should be added to all events within a single page,
 * including errors, events, and browser interactions.
 */
const moduleGlobal: {
  customPageAttributes: NewRelicEventAttributes;
} = {
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
 */
function newrelicReady() {
  return (
    // Can't use optional chaining here because you get a ReferenceError when `window` is never declared
    typeof window !== "undefined" && typeof window.newrelic !== "undefined"
  );
}

/**
 * Track a JS error
 * @see https://docs.newrelic.com/docs/browser/new-relic-browser/browser-agent-spa-api/noticeerror-browser-agent-api
 */
function noticeError(
  error: unknown,
  customAttributes: NewRelicEventAttributes = {}
) {
  if (!newrelicReady()) return;

  if (error instanceof Error) {
    window.newrelic?.noticeError(error, {
      ...moduleGlobal.customPageAttributes,
      ...customAttributes,
      environment: process.env.buildEnv || "",
      portalReleaseVersion: process.env.releaseVersion || "",
    });
  } else {
    trackEvent(
      "Tried tracking error, but it wasn't an Error instance. See errorContents.",
      {
        errorContents: JSON.stringify(error),
      }
    );
  }
}

/**
 * Track Single Page App (SPA) route changes in New Relic and give them more accurate names.
 * @see https://docs.newrelic.com/docs/browser/new-relic-browser/guides/guide-using-browser-spa-apis
 * @see https://docs.newrelic.com/docs/browser/new-relic-browser/browser-agent-spa-api/spa-set-current-route-name
 * @param routeName Route names should represent a routing pattern
 * @param customPageAttributes Optional custom attributes to set for the page and for subsequent events on the same page
 *  rather than a specific resource. For example /claims/:id rather than /claims/123
 */
function startPageView(
  routeName: string,
  customPageAttributes?: NewRelicEventAttributes
) {
  if (newrelicReady()) {
    // First end previous interaction if that's still in progress
    window.newrelic?.interaction().end();

    moduleGlobal.customPageAttributes = customPageAttributes || {};
    window.newrelic?.interaction();
    setPageAttributesOnInteraction();
    window.newrelic?.setCurrentRouteName(routeName);
  }
}

/**
 * Track a page action or event
 * @see https://docs.newrelic.com/docs/browser/new-relic-browser/browser-agent-spa-api/add-page-action
 * @param name - Name or category of the action
 */
function trackEvent(
  name: string,
  customAttributes: NewRelicEventAttributes = {}
) {
  if (newrelicReady()) {
    window.newrelic?.addPageAction(name, {
      ...moduleGlobal.customPageAttributes,
      ...customAttributes,
      environment: process.env.buildEnv || "",
      portalReleaseVersion: process.env.releaseVersion || "",
    });
  }
}

/**
 * For New Relic, Fetch requests are only recorded if they are executed during a BrowserInteraction event,
 * which by default happens during the initial page load and any time the route is changed. That means
 * for other cases, we need to manually initiate a BrowserInteraction so the request is tracked.
 * @see https://docs.newrelic.com/docs/browser/new-relic-browser/troubleshooting/troubleshoot-ajax-data-collection
 * @param requestName - URL being fetched (if known) or name representing the request
 * @example trackFetchRequest('https://paidleave-api.mass.gov/applications'); request(...);
 */
function trackFetchRequest(requestName: string) {
  if (newrelicReady()) {
    // First end previous interaction if that's still in progress
    window.newrelic?.interaction().end();

    const trackedName = requestName.replace("https://", "");
    window.newrelic?.interaction().setName(`fetch: ${trackedName}`);
    window.newrelic
      ?.interaction()
      .setAttribute("environment", process.env.buildEnv);
    window.newrelic
      ?.interaction()
      .setAttribute("portalReleaseVersion", process.env.releaseVersion);
    setPageAttributesOnInteraction();
    window.newrelic?.interaction().save();
  }
}

/**
 * Ensure Cognito AJAX requests are traceable in New Relic
 * @param action - name of the Cognito method being called
 */
function trackAuthRequest(action: string) {
  trackFetchRequest(`cognito ${action}`);
}

/**
 * Call this after a fetch request being tracked with trackFetchRequest has completed,
 * so subsequent requests made by third-party scripts (e.g Google Analytics) don't get
 * tracked under the same browser interaction.
 */
function markFetchRequestEnd() {
  if (newrelicReady()) {
    window.newrelic?.interaction().end();
  }
}

function setPageAttributesOnInteraction() {
  if (newrelicReady()) {
    for (const [name, value] of Object.entries(
      moduleGlobal.customPageAttributes
    )) {
      window.newrelic?.interaction().setAttribute(name, value);
    }
  }
}

export default {
  initialize,
  markFetchRequestEnd,
  noticeError,
  startPageView,
  trackAuthRequest,
  trackEvent,
  trackFetchRequest,
};
