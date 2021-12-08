/**
 * Infra-test environment's public environment variables.
 * WARNING: No secrets!
 * Only store non-secrets here. Everything in this file can be included in build artifacts.
 */
 module.exports = {
    envName: "infra-test",
    // API Trn2 environment (https://lwd.atlassian.net/wiki/spaces/DD/pages/246612440/Environments)
    apiUrl: "https://paidleave-api-infra-test.dfml.eol.mass.gov/api/v1",
    awsConfig: {
      // Cognito Infra-test environment (must match whatever API environment we're targeting)
      cognitoUserPoolId: "us-east-1_8OEJk2XeD",
      cognitoUserPoolWebClientId: "5pf01ur8rsdoumtu3ta8jvqbsj",
    },
    domain: "paidleave-infra-test.dfml.eol.mass.gov",
    gtmConfig: {},
    newRelicAppId: "847219405",
  };
