/**
 * Training environment's public environment variables.
 * WARNING: No secrets!
 * Only store non-secrets here. Everything in this file can be included in build artifacts.
 */
module.exports = {
  envName: "training",
  // API Training environment (https://lwd.atlassian.net/wiki/spaces/DD/pages/246612440/Environments)
  apiUrl: "https://paidleave-api-training.mass.gov/api/v1",
  awsConfig: {
    // Cognito Training environment (must match whatever API environment we're targeting)
    cognitoUserPoolId: "us-east-1_gHLjkp4A8",
    cognitoUserPoolWebClientId: "2hr6bckdopamvq92jahr542p5p",
  },
  domain: "paidleave-training.mass.gov",
  gtmConfig: {},
  newRelicAppId: "982303878",
};
