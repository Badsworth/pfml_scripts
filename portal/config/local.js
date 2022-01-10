// @ts-check

/**
 * Local development environment's public environment variables [Version for when you want to connect local frontend to local backend]
 * WARNING: No secrets!
 * Only store non-secrets here. Everything in this file can be included in build artifacts.
 * @type {Record<string, string>}
 */
const config = {
  envName: "local",
  domain: "localhost",
  apiUrl: "http://localhost:1550/v1",
  // Cognito Stage environment (to match backend local defaults)
  awsCognitoUserPoolId: "us-east-1_HpL4XslLg",
  awsCognitoUserPoolWebClientId: "10rjcp71r8bnk4459c67bn18t8",
};

module.exports = config;
