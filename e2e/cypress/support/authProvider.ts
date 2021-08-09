// Configure Amplify for Auth behavior throughout the app
// Auth.configure({
//   cookieStorage: {
//     domain: config("PORTAL_BASEURL"),
//     // Require cookie transmission over a secure protocol (https) outside of local dev.
//     // We use env.domain instead of env.NODE_ENV here since our end-to-end test suite is
//     // ran against a production build on localhost.
//     secure: process.env.domain !== "localhost",
//     // Set cookie expiration to expire at end of session.
//     // (Amplify defaults to a year, which is wild)
//     expires: null,
//     // path: '/', (optional)
//   },
//   mandatorySignIn: false,
//   region: "us-east-1",
//   userPoolId: config("COGNITO_POOL"),
//   userPoolWebClientId: config("COGNITO_CLIENTID"),
// });

import { CognitoUserSession } from "amazon-cognito-identity-js";

// Amazon Cognito
Cypress.Commands.add("loginByCognitoApi", (username, password) => {
  const log = Cypress.log({
    displayName: "COGNITO LOGIN",
    message: [`🔐 Authenticating | ${username}`],
    // @ts-ignore
    autoEnd: false,
  });

  log.snapshot("before");

  cy.task("getUserSession", { username, password }).then((cognitoResponse) => {
    const userSession: CognitoUserSession =
      cognitoResponse as CognitoUserSession;
    const keyPrefix = userSession.idToken.payload.aud;
    const username = userSession.idToken.payload.sub;
    console.log(userSession);
    console.log(userSession.accessToken);
    console.log(userSession.idToken);
    console.log(userSession.refreshToken);
    const keyPrefixWithUsername = `${keyPrefix}.${username}`;

    cy.setCookie(
      `CognitoIdentityServiceProvider.${keyPrefixWithUsername}.idToken`,
      userSession.idToken.jwtToken
    );

    cy.setCookie(
      `CognitoIdentityServiceProvider.${keyPrefixWithUsername}.accessToken`,
      userSession.accessToken.jwtToken
    );

    cy.setCookie(
      `CognitoIdentityServiceProvider.${keyPrefixWithUsername}.refreshToken`,
      userSession.refreshToken.token
    );

    cy.setCookie(
      `CognitoIdentityServiceProvider.${keyPrefixWithUsername}.clockDrift`,
      "2"
    );

    cy.setCookie(
      `CognitoIdentityServiceProvider.${keyPrefix}.LastAuthUser`,
      username
    );

    cy.setCookie("amplify-authenticator-authState", "signedIn");
    cy.setCookie("amplify-signin-with-hostedUI", "false");
    log.snapshot("after");
    log.end();
  });
});
