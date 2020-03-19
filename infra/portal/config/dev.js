/*
WARNING: No secrets!
Only store non-secrets here. Everything in this file can be included in build artifacts.
*/
module.exports = {
  envName: "Development",
  awsConfig: {
    Auth: {
      region: "us-east-1",
      userPoolId: "us-east-1_WF0fMrnQ4",
      userPoolWebClientId: "2lltjbpjeur6hcpshautn1e11f",
      mandatorySignIn: false,
    },
  },
};
