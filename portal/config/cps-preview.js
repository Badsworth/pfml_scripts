/**
 * CPS-Preview environment's public environment variables.
 * WARNING: No secrets!
 * Only store non-secrets here. Everything in this file can be included in build artifacts.
 */
module.exports = {
  envName: "cps-preview",
  // API CPS-Preview environment (https://lwd.atlassian.net/wiki/spaces/DD/pages/246612440/Environments)
  apiUrl: "https://paidleave-api-cps-preview.eol.mass.gov/api/v1",
  awsConfig: {
    // Cognito CPS-Preview environment (must match whatever API environment we're targeting)
    cognitoUserPoolId: "us-east-1_1OVYp4aZo",
    cognitoUserPoolWebClientId: "59oeobfn0759c8166pjh381joc",
  },
  domain: "paidleave-cps-preview.eol.mass.gov",
  gtmConfig: {},
  newRelicAppId: "1275659093",
  experianApiKey: "961b1b04-80cc-4ad5-85e3-4409430a1d6d",
};
