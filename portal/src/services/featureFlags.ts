/**
 * @file Methods for checking and setting feature flags
 */
import Cookies from "js-cookie";
import tracker from "./tracker";

const featureFlagsParamName = "_ff";

/**
 * Check whether a feature flag is enabled
 * @param {string} name - Feature flag name
 * @returns {boolean} Whether the flag is defined and enabled
 */
export function isFeatureEnabled(name) {
  const cookieFlags = getCookieFlags();
  if (cookieFlags.hasOwnProperty(name)) return cookieFlags[name];

  // https://nextjs.org/docs/api-reference/next.config.js/environment-variables
  const environmentFlags = process.env.featureFlags;
  return environmentFlags[name];
}

/**
 * Get the feature flags that are stored in the cookie
 * @returns {object} - name/value for each feature flag
 */
function getCookieFlags() {
  const cookie = Cookies.get(featureFlagsParamName);

  if (!cookie) return {};

  return JSON.parse(cookie);
}

/**
 * Check if a flag is defined at the environment-level, indicating
 * that it's a valid flag that we can override through the query string.
 * @param {string} flagName
 * @returns {boolean}
 */
function flagExistsInEnvironment(flagName) {
  // https://nextjs.org/docs/api-reference/next.config.js/environment-variables
  const environmentFlags = process.env.featureFlags;

  if (environmentFlags.hasOwnProperty(flagName)) return true;

  // eslint-disable-next-line no-console
  console.warn(`${flagName} ignored`);
  return false;
}

/**
 * Update the feature flags cookie, so that the user can override environment-level
 * feature flags. Expects a querystring with a param of _ff.
 * For example, example.com?_ff=showSite:true;enableClaimFlow:false would enable
 * showSite and disable enableClaimFlow
 * @param {URLSearchParams} searchParams
 */
export function storeFeatureFlagsFromQuery(searchParams) {
  if (!searchParams) return;

  const paramValue = searchParams.get(featureFlagsParamName);
  if (!paramValue) return;

  // Convert the query string into array of key/value pairs
  // a:valA;b:valB => [ [a, valA], [b, valB] ]
  const flags = paramValue.split(";").map((value) => value.split(":"));

  flags
    .filter(([flagName, flagValue]) => {
      // Prevent someone from setting arbitrary feature flags
      return flagValue && flagExistsInEnvironment(flagName);
    })
    .forEach(([flagName, flagValue]) => {
      updateCookieWithFlag(flagName, flagValue);
    });

  // Track when someone sets feature flag(s) through their browser
  tracker.trackEvent("manual_feature_flags", { flags });
}

/**
 * Updates the feature flag cookie based on the given flag name/value.
 * This merges the given flag with any existing cookie value.
 * @param {string} flagName
 * @param {string} flagValue
 */
export function updateCookieWithFlag(flagName, flagValue) {
  const cookieFlags = getCookieFlags();

  if (flagValue === "reset") delete cookieFlags[flagName];

  if (["true", "false"].includes(flagValue)) {
    cookieFlags[flagName] = flagValue === "true";
  }

  Cookies.set(featureFlagsParamName, JSON.stringify(cookieFlags), {
    expires: 180, // days
  });
}
