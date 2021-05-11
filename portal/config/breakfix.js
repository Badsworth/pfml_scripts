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
    cognitoUserPoolId: "us-east-1_Bi6tPV5hz",
    cognitoUserPoolWebClientId: "606qc6fmb1sn3pcujrav20h66l",
  },
  domain: "paidleave-breakfix.eol.mass.gov",
  gtmConfig: {},
  newRelicAppId: "1263903855",
};
