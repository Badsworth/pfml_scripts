/*
WARNING: No secrets!
Only store non-secrets here. Everything in this file can be included in build artifacts.
*/
module.exports = {
  envName: "Development",
  awsConfig: {
    Auth: {
      region: "us-east-1",
      userPoolId: "us-east-1_s2X4okD8q",
      userPoolWebClientId: "66eoqh5el29kt5v3hcl80jta44",
      mandatorySignIn: false,
      oauth: {
        domain: "massgov-pfml-sandbox-v2.auth.us-east-1.amazoncognito.com",
        scope: [
          "phone",
          "email",
          "profile",
          "openid",
          "aws.cognito.signin.user.admin"
        ],
        redirectSignIn: "http://localhost:3000",
        redirectSignOut: "http://localhost:3000",
        responseType: "code"
      }
    }
  }
};
