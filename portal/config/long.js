// @ts-check

/**
 * Long environment's public environment variables.
 * WARNING: No secrets!
 * Only store non-secrets here. Everything in this file can be included in build artifacts.
 * @type {Record<string, string>}
 */
const config = {
  envName: "long",
  // API Long environment (https://lwd.atlassian.net/wiki/spaces/DD/pages/246612440/Environments)
  apiUrl: "https://paidleave-api-long.dfml.eol.mass.gov/api/v1",
  // Cognito Long environment (must match whatever API environment we're targeting)
  awsCognitoUserPoolId: "us-east-1_FADLpF6um",
  awsCognitoUserPoolWebClientId: "1ufb6r40s1ad0evjffvdtl3113",
  domain: "paidleave-long.dfml.eol.mass.gov",
  gtmConfigAuth: "",
  newRelicAppId: "1588653703",
};

module.exports = config;
