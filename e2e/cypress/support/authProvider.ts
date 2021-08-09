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

  cy.task("getUserSession", { username, password }).then((sessionCookies) => {
    sessionCookies.forEach(([name, value]) =>
      cy.setCookie(name, value, { log: false })
    );
    log.snapshot("after");
    log.end();
  });
});
