// @ts-check

/**
 * UAT environment's public environment variables.
 * WARNING: No secrets!
 * Only store non-secrets here. Everything in this file can be included in build artifacts.
 * @type {Record<string, string>}
 */
const config = {
  envName: "uat",
  // API UAT environment (https://lwd.atlassian.net/wiki/spaces/DD/pages/246612440/Environments)
  apiUrl: "https://paidleave-api-uat.mass.gov/api/v1",
  // Cognito UAT environment (must match whatever API environment we're targeting)
  awsCognitoUserPoolId: "us-east-1_29j6fKBDT",
  awsCognitoUserPoolWebClientId: "1ajh0c38bs21k60bjtttegspvp",
  domain: "paidleave-uat.mass.gov",
  gtmConfigAuth: "",
  newRelicAppId: "1062794160",
};

module.exports = config;
