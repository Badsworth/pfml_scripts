/**
 * Performance environment's public environment variables.
 * WARNING: No secrets!
 * Only store non-secrets here. Everything in this file can be included in build artifacts.
 */
module.exports = {
  envName: "performance",
  // API Performance environment (https://lwd.atlassian.net/wiki/spaces/DD/pages/246612440/Environments)
  apiUrl:
    "https://lk64ifbnn4.execute-api.us-east-1.amazonaws.com/performance/api/v1",
  awsConfig: {
    // Cognito Performance environment (must match whatever API environment we're targeting)
    cognitoUserPoolId: "us-east-1_0jv6SlemT",
    cognitoUserPoolWebClientId: "1ps8bs9s5ns4f6qamj6qn6qd3",
  },
  domain: "dijouhh49zeeb.cloudfront.net",
  gtmConfig: {},
  newRelicAppId: "982305384",
};
