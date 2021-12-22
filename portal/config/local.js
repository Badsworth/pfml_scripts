/**
 * Local development environment's public environment variables [Version for when you want to connect local frontend to local backend]
 * WARNING: No secrets!
 * Only store non-secrets here. Everything in this file can be included in build artifacts.
 */
module.exports = {
  envName: "local",
  domain: "localhost",
  apiUrl: "http://localhost:1550/v1",
  awsConfig: {
    cognitoRegion: "us-east-1",
    // Cognito Stage environment (to match backend local defaults)
    cognitoUserPoolId: "us-east-1_HpL4XslLg",
    cognitoUserPoolWebClientId: "10rjcp71r8bnk4459c67bn18t8",
  },
};
