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
  apiUrl: "https://paidleave-api-stage.mass.gov/api/v1",
  awsConfig: {
    cognitoRegion: "us-east-1",
    // Cognito Stage environment (must match whatever API environment we're targeting)
    cognitoUserPoolId: "us-east-1_HpL4XslLg",
    cognitoUserPoolWebClientId: "10rjcp71r8bnk4459c67bn18t8",
  },
  // Enable the maintenance page on these routes:
  // See docs/portal/maintenance-pages.md for details.
  maintenancePageRoutes: ["/*"],
  maintenanceStart: "2021-05-04T21:00:00-04:00",
  maintenanceEnd: "2021-05-04T23:30:00-04:00",
  newRelicAppId: null,
  sentryDsn:
    "https://3c7da99697784a3dab944dec622d1b50@o514801.ingest.sentry.io/5620266",
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
