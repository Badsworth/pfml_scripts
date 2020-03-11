/*
WARNING: No secrets!
Only store non-secrets here. Everything in this file can be included in build artifacts.
*/
module.exports = {
  envName: "Test",
  awsConfig: {
    Auth: {
      region: "us-east-1",
      userPoolId: "us-east-1_s2X4okD8q",
      userPoolWebClientId: "66eoqh5el29kt5v3hcl80jta44",
      mandatorySignIn: false,
    },
  },
};
