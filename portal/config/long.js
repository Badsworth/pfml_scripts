/**
 * Long environment's public environment variables.
 * WARNING: No secrets!
 * Only store non-secrets here. Everything in this file can be included in build artifacts.
 */
 module.exports = {
    envName: "long",
    // API Long environment (https://lwd.atlassian.net/wiki/spaces/DD/pages/246612440/Environments)
    apiUrl: "https://paidleave-api-long.dfml.eol.mass.gov/api/v1",
    awsConfig: {
      // Cognito Long environment (must match whatever API environment we're targeting)
      cognitoUserPoolId: "us-east-1_FADLpF6um",
      cognitoUserPoolWebClientId: "1ufb6r40s1ad0evjffvdtl3113",
    },
    domain: "paidleave-long.dfml.eol.mass.gov",
    gtmConfig: {},
    newRelicAppId: "1531932432",
  };
  