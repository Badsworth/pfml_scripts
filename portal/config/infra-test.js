// @ts-check

/**
 * Infra-test environment's public environment variables.
 * WARNING: No secrets!
 * Only store non-secrets here. Everything in this file can be included in build artifacts.
 * @type {Record<string, string>}
 */
const config = {
  envName: "infra-test",
  // API Trn2 environment (https://lwd.atlassian.net/wiki/spaces/DD/pages/246612440/Environments)
  apiUrl: "https://paidleave-api-infra-test.dfml.eol.mass.gov/api/v1",
  // Cognito Infra-test environment (must match whatever API environment we're targeting)
  awsCognitoUserPoolId: "us-east-1_8OEJk2XeD",
  awsCognitoUserPoolWebClientId: "5pf01ur8rsdoumtu3ta8jvqbsj",
  domain: "paidleave-infra-test.dfml.eol.mass.gov",
  gtmConfigAuth: "",
  newRelicAppId: "847219405",
};

module.exports = config;
