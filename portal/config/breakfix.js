/**
 * Breakfix environment's public environment variables.
 * WARNING: No secrets!
 * Only store non-secrets here. Everything in this file can be included in build artifacts.
 */
module.exports = {
  envName: "breakfix",
  // API Breakfix environment (https://lwd.atlassian.net/wiki/spaces/DD/pages/246612440/Environments)
  apiUrl: "https://paidleave-api-breakfix.eol.mass.gov/api/v1",
  awsConfig: {
    // Cognito Breakfix environment (must match whatever API environment we're targeting)
    cognitoUserPoolId: "us-east-1_ZM6ztWTcs",
    cognitoUserPoolWebClientId: "1ijqntaslj2des88rlrdvoqlm5",
  },
  domain: "paidleave-breakfix.eol.mass.gov",
  gtmConfig: {},
  newRelicAppId: "1263903855",
};
