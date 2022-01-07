// @ts-check

/**
 * Performance environment's public environment variables.
 * WARNING: No secrets!
 * Only store non-secrets here. Everything in this file can be included in build artifacts.
 * @type {Record<string, string>}
 */
const config = {
  envName: "performance",
  // API Performance environment (https://lwd.atlassian.net/wiki/spaces/DD/pages/246612440/Environments)
  apiUrl: "https://paidleave-api-performance.mass.gov/api/v1",
  // Cognito Performance environment (must match whatever API environment we're targeting)
  awsCognitoUserPoolId: "us-east-1_0jv6SlemT",
  awsCognitoUserPoolWebClientId: "1ps8bs9s5ns4f6qamj6qn6qd3",
  domain: "paidleave-performance.mass.gov",
  gtmConfigAuth: "",
  newRelicAppId: "982305384",
};

module.exports = config;
