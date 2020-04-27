/**
 * Stage environment's public environment variables.
 * WARNING: No secrets!
 * Only store non-secrets here. Everything in this file can be included in build artifacts.
 */
module.exports = {
  envName: "stage",
  awsConfig: {
    Auth: {
      region: "us-east-1",
      userPoolId: "us-east-1_HpL4XslLg",
      userPoolWebClientId: "10rjcp71r8bnk4459c67bn18t8",
      mandatorySignIn: false,
    },
  },
};
