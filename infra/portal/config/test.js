/*
WARNING: No secrets!
Only store non-secrets here. Everything in this file can be included in build artifacts.
*/
module.exports = {
  envName: "Test",
  awsConfig: {
    Auth: {
      region: "us-east-1",
      userPoolId: "us-east-1_GNTcmhyhe",
      userPoolWebClientId: "6350hg4umjm2br8sqjl7urm5eb",
      mandatorySignIn: false,
    },
  },
};
