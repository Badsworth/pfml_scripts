/**
 * Check whether a feature flag is enabled
 * @param {string} name - Feature flag name
 * @returns {boolean} Whether the flag is defined and enabled
 */
function isFeatureEnabled(name) {
  // // https://nextjs.org/docs/api-reference/next.config.js/environment-variables
  const environmentFlags = process.env.featureFlags;

  // TODO: Check if a feature flag is set in a cookie and use it instead,
  // otherwise fallback to the flags value in the environment variable
  // https://lwd.atlassian.net/browse/CP-28
  return environmentFlags[name];
}

export default isFeatureEnabled;
