// @ts-check

/**
 * CPS-Preview environment's public environment variables.
 * WARNING: No secrets!
 * Only store non-secrets here. Everything in this file can be included in build artifacts.
 * @type {Record<string, string>}
 */
const config = {
  envName: "cps-preview",
  // API CPS-Preview environment (https://lwd.atlassian.net/wiki/spaces/DD/pages/246612440/Environments)
  apiUrl: "https://paidleave-api-cps-preview.eol.mass.gov/api/v1",
  // Cognito CPS-Preview environment (must match whatever API environment we're targeting)
  awsCognitoUserPoolId: "us-east-1_1OVYp4aZo",
  awsCognitoUserPoolWebClientId: "59oeobfn0759c8166pjh381joc",
  domain: "paidleave-cps-preview.eol.mass.gov",
  gtmConfigAuth: "",
  newRelicAppId: "1275659093",
};

module.exports = config;
