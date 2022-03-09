// @ts-check

/**
 * Breakfix environment's public environment variables.
 * WARNING: No secrets!
 * Only store non-secrets here. Everything in this file can be included in build artifacts.
 * @type {Record<string, string>}
 */
const config = {
  envName: "breakfix",
  // API Breakfix environment (https://lwd.atlassian.net/wiki/spaces/DD/pages/246612440/Environments)
  apiUrl: "https://paidleave-api-breakfix.eol.mass.gov/api/v1",
  // Cognito Breakfix environment (must match whatever API environment we're targeting)
  awsCognitoUserPoolId: "us-east-1_ZM6ztWTcs",
  awsCognitoUserPoolWebClientId: "1ijqntaslj2des88rlrdvoqlm5",
  domain: "paidleave-breakfix.eol.mass.gov",
  gtmConfigAuth: "",
  newRelicAppId: "1263903855",
};

module.exports = config;
