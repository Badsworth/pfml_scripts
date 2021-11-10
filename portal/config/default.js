/**
 * Default environment variables for all environments. Individual
 * environment files (e.g production.js) can override these variables,
 * in which case the individual environment's variables are merged
 * with these, in config/index.js.
 *
 * WARNING: No secrets!
 * Only store non-secrets here. Everything in this file can be included in build artifacts.
 */
module.exports = {
  // We target the API stage environment for the systems we're dependent on,
  // even in dev and test. Read more here: https://lwd.atlassian.net/wiki/spaces/DD/pages/246612440/Environments
  apiUrl: "http://localhost:1550/v1",
  awsConfig: {
    cognitoRegion: "us-east-1",
    // MFA Cognito
    cognitoUserPoolId: "us-east-1_Ok2yc8UXd",
    cognitoUserPoolWebClientId: "5q860cvap9p2se09q284thas48",
  },
  newRelicAppId: null,
  gtmConfig: {
    // Google Tag Manager Stage environment
    auth: "9Gb_47rccihIuwtcFdJy4w",
    preview: "env-4",
  },
  session: {
    // 30 minutes
    secondsOfInactivityUntilLogout: 30 * 60,
  },
};
