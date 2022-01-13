// @ts-check

/**
 * Default environment variables for all environments. Individual
 * environment files (e.g production.js) can override these variables,
 * in which case the individual environment's variables are merged
 * with these, in config/index.js.
 *
 * WARNING: No secrets!
 * Only store non-secrets here. Everything in this file can be included in build artifacts.
 * @type {Record<string, string>}
 */
const config = {
  // We target the API stage environment for the systems we're dependent on,
  // even in dev and test. Read more here: https://lwd.atlassian.net/wiki/spaces/DD/pages/246612440/Environments
  apiUrl: "https://paidleave-api-stage.mass.gov/api/v1",
  awsCognitoRegion: "us-east-1",
  // Cognito Stage environment (must match whatever API environment we're targeting)
  awsCognitoUserPoolId: "us-east-1_HpL4XslLg",
  awsCognitoUserPoolWebClientId: "10rjcp71r8bnk4459c67bn18t8",
  // PFML API Gateway has a 10mb payload size limit, so we shouldn't attempt to send files beyond this.
  // https://docs.aws.amazon.com/apigateway/latest/developerguide/limits.html#http-api-quotas
  fileSizeMaxBytesApiGateway: "10000000",
  // Fineos uploads are Base64-encoded. Their limit is 6mb. 4.5mb is the max size before base64 encoding.
  fileSizeMaxBytesFineos: "4500000",
  newRelicAppId: "",
  // Google Tag Manager Stage environment
  gtmConfigAuth: "9Gb_47rccihIuwtcFdJy4w",
  gtmConfigPreview: "env-4",
  // 30 minutes:
  secondsOfInactivityUntilLogout: "1800",
};

module.exports = config;
