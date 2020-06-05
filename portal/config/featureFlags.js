/**
 * Feature flags. A feature flag can be enabled/disabled at the environment level.
 * Its value will either be true or false. Environments can override this value.
 * @see ../../docs/portal/feature-flags.md
 */
const flagsConfig = {
  // Define a default or all feature flags here.
  // Environments will fallback to these default values.
  defaults: {
    example: false,
    // When this flag is enabled, the user can see the site.
    // To immediately hide the site from people who previously overrode this
    // flag in a cookie, you can rename this flag to something else (and also
    // update the reference to it in _app.js), but try to keep it prefixed with pfml.
    // https://lwd.atlassian.net/browse/CP-459
    pfmlTerriyay: false,
    // When unrestrictedClaimFlow is enabled, a user can proceed through the
    // full claim flow. This is in place to prevent pilot users from going to
    // screens that we're not yet ready to pilot.
    unrestrictedClaimFlow: true,
  },
  // Environments can optionally override a default feature flag below.
  // The environment keys should use the same envName defined in
  // environment config files.
  development: {
    example: true,
    pfmlTerriyay: true,
  },
};

/**
 * Merges the default feature flags with any environment-specific overrides
 * @param {string} env - Environment name
 * @returns {object} Feature flags for the given environment
 */
function featureFlags(env) {
  return Object.assign({}, flagsConfig.defaults, flagsConfig[env]);
}

module.exports = featureFlags;
