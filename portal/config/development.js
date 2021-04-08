/**
 * Local development environment's public environment variables.
 * WARNING: No secrets!
 * Only store non-secrets here. Everything in this file can be included in build artifacts.
 */
module.exports = {
  // Not finding what you're looking for? Check default.js
  envName: "development",
  domain: "localhost",
  gtmConfig: {
    // Google Tag Manager Test environment (for testing changes to GTM configuration)
    // auth: "SiSVu0U7VjoUiceaFWQeqA",
    // preview: "env-5",
  },
  // This is the same New Relic app as the Test environment
  newRelicAppId: "847038274",
};
