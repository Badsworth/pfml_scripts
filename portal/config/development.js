/**
 * Local development environment's public environment variables.
 * WARNING: No secrets!
 * Only store non-secrets here. Everything in this file can be included in build artifacts.
 */
module.exports = {
  envName: "development",
  // API Stage environment (https://lwd.atlassian.net/wiki/spaces/DD/pages/246612440/Environments)
  apiUrl: "https://paidleave-api-stage.mass.gov/api/v1",
  awsConfig: {
    Auth: {
      region: "us-east-1",
      // Cognito Stage environment (must match whatever API environment we're targeting)
      userPoolId: "us-east-1_HpL4XslLg",
      userPoolWebClientId: "10rjcp71r8bnk4459c67bn18t8",
      mandatorySignIn: false,
    },
  },
  gtmConfig: {
    // Google Tag Manager Stage environment
    auth: "9Gb_47rccihIuwtcFdJy4w",
    preview: "env-4",

    // Google Tag Manager Test environment (for testing changes to GTM configuration)
    // auth: "SiSVu0U7VjoUiceaFWQeqA",
    // preview: "env-5",
  },
  // This is the same New Relic app as the Test environment
  newRelicAppId: "706309942",
};
