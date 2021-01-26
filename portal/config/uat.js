/**
 * UAT environment's public environment variables.
 * WARNING: No secrets!
 * Only store non-secrets here. Everything in this file can be included in build artifacts.
 */
module.exports = {
  envName: "uat",
  // API UAT environment (https://lwd.atlassian.net/wiki/spaces/DD/pages/246612440/Environments)
  apiUrl: "https://paidleave-api-uat.mass.gov/api/v1",
  awsConfig: {
    // Cognito UAT environment (must match whatever API environment we're targeting)
    cognitoUserPoolId: "us-east-1_29j6fKBDT",
    cognitoUserPoolWebClientId: "1ajh0c38bs21k60bjtttegspvp",
  },
  domain: "paidleave-uat.mass.gov",
  gtmConfig: {},
  newRelicAppId: "1062794160",
};
