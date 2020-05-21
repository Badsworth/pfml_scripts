/**
 * Local development environment's public environment variables.
 * WARNING: No secrets!
 * Only store non-secrets here. Everything in this file can be included in build artifacts.
 */
module.exports = {
  envName: "development",
  // API Stage environment (https://lwd.atlassian.net/wiki/spaces/DD/pages/246612440/Environments)
  apiUrl: "https://hxrjel1aeb.execute-api.us-east-1.amazonaws.com/stage/api/v1",
  awsConfig: {
    Auth: {
      region: "us-east-1",
      userPoolId: "us-east-1_HhQSLYSIe",
      userPoolWebClientId: "7sjb96tvg8251lrq5vdk7de9",
      mandatorySignIn: false,
    },
  },
};
