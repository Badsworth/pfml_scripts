/**
 * Prod environment's public environment variables.
 * WARNING: No secrets!
 * Only store non-secrets here. Everything in this file can be included in build artifacts.
 */
module.exports = {
  envName: "prod",
  // API Production environment (https://lwd.atlassian.net/wiki/spaces/DD/pages/246612440/Environments)
  apiUrl: "https://paidleave-api.mass.gov/api/v1",
  awsConfig: {
    // Cognito Production environment (must match whatever API environment we're targeting)
    cognitoUserPoolId: "us-east-1_UwxnhD1cG",
    cognitoUserPoolWebClientId: "64p5sdtqul5a4pn3ikbscjhujn",
  },
  domain: "paidleave.mass.gov",
  // Google Tag Manager Prod environment
  gtmConfig: {
    auth: "M4sQ_RNEqsKttKJFMho1Mg",
    preview: "env-3",
  },
  newRelicAppId: "847045300",
};