/**
 * Prod environment's public environment variables.
 * WARNING: No secrets!
 * Only store non-secrets here. Everything in this file can be included in build artifacts.
 */
module.exports = {
  envName: "prod",
  awsConfig: {
    Auth: {
      region: "us-east-1",
      userPoolId: "us-east-1_7wHRApy7h",
      userPoolWebClientId: "3hrdqrg9s98lkkrp821ge0fqu3",
      mandatorySignIn: false,
    },
  },
};
