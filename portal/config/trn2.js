/**
 * Trn2 environment's public environment variables.
 * WARNING: No secrets!
 * Only store non-secrets here. Everything in this file can be included in build artifacts.
 */
 module.exports = {
    envName: "trn2",
    // API Trn2 environment (https://lwd.atlassian.net/wiki/spaces/DD/pages/246612440/Environments)
    apiUrl: "https://paidleave-api-trn2.dfml.eol.mass.gov/api/v1",
    awsConfig: {
      // Cognito Trn2 environment (must match whatever API environment we're targeting)
      cognitoUserPoolId: "us-east-1_oxOGrdAe8",
      cognitoUserPoolWebClientId: "16oll6nm4ifkik83b7c3s2a0ro",
    },
    domain: "paidleave-trn2.dfml.eol.mass.gov",
    gtmConfig: {},
    newRelicAppId: "1545153521",
  };
