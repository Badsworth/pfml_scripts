/**
 * Test environment's public environment variables.
 * WARNING: No secrets!
 * Only store non-secrets here. Everything in this file can be included in build artifacts.
 */
module.exports = {
  // Not finding what you're looking for? Check default.js
  // apiUrl: "https://paidleave-api-test.mass.gov/api/v1",
  envName: "test",
  domain: "paidleave-test.mass.gov",
  newRelicAppId: "847038274",
  // awsConfig: {
  //   cognitoRegion: "us-east-1",
  //   // Cognito test environment (must match whatever API environment we're targeting)
  //   cognitoUserPoolId: "us-east-1_HhQSLYSIe",
  //   cognitoUserPoolWebClientId: "7sjb96tvg8251lrq5vdk7de9",
  // },
};
