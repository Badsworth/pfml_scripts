/**
 * Test environment's public environment variables.
 * WARNING: No secrets!
 * Only store non-secrets here. Everything in this file can be included in build artifacts.
 */
module.exports = {
  envName: "test",
  apiUrl: "https://67385ye4yb.execute-api.us-east-1.amazonaws.com/test/api/v1/",
  awsConfig: {
    Auth: {
      region: "us-east-1",
      userPoolId: "us-east-1_dbBlM71TW",
      userPoolWebClientId: "15k7b04brctr5gj79nm63j2tjl",
      mandatorySignIn: false,
    },
  },
};
