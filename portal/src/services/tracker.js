/**
 * @file Wrapper methods around our monitoring service. Methods in here should
 * handle a scenario where the monitoring service is blocked by things like an ad blocker.
 */

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
    newrelic.noticeError(error, customAttributes);
  }
}

/**
 * Give a route in New Relic more accurate names.
 * @see https://docs.newrelic.com/docs/browser/new-relic-browser/browser-agent-spa-api/spa-set-current-route-name
 * @param {string} routeName - Route names should represent a routing pattern
 *  rather than a specific resource. For example /claims/:id rather than /claims/123
 */
function setCurrentRouteName(routeName) {
  if (newrelicReady()) {
    newrelic.setCurrentRouteName(routeName);
  }
}

export default { noticeError, setCurrentRouteName };
