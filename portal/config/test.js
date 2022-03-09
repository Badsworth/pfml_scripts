// @ts-check

/**
 * Test environment's public environment variables.
 * WARNING: No secrets!
 * Only store non-secrets here. Everything in this file can be included in build artifacts.
 * @type {Record<string, string>}
 */
const config = {
  // Not finding what you're looking for? Check default.js
  // apiUrl: "https://paidleave-api-test.mass.gov/api/v1",
  envName: "test",
  domain: "paidleave-test.mass.gov",
  newRelicAppId: "847038274",
  // TODO (CP-1362): Revert temporary switch to Test environment
  apiUrl: "https://paidleave-api-test.mass.gov/api/v1",
  // Cognito test environment (must match whatever API environment we're targeting)
  // TODO (CP-1362): Revert temporary switch to Test environment
  awsCognitoUserPoolId: "us-east-1_HhQSLYSIe",
  // TODO (CP-1362): Revert temporary switch to Test environment
  awsCognitoUserPoolWebClientId: "7sjb96tvg8251lrq5vdk7de9",
};

module.exports = config;
