import Auth, { CognitoUser } from "@aws-amplify/auth";
import config from "../../src/config";
// Configure Amplify for Auth behavior throughout the app
Auth.configure({
  cookieStorage: {
    domain: process.env.domain,
    // Require cookie transmission over a secure protocol (https) outside of local dev.
    // We use env.domain instead of env.NODE_ENV here since our end-to-end test suite is
    // ran against a production build on localhost.
    secure: process.env.domain !== "localhost",
    // Set cookie expiration to expire at end of session.
    // (Amplify defaults to a year, which is wild)
    expires: null,
    // path: '/', (optional)
  },
  mandatorySignIn: false,
  region: "us-east-1",
  userPoolId: config("COGNITO_POOL"),
  userPoolWebClientId: config("COGNITO_CLIENTID"),
});

// Amazon Cognito
Cypress.Commands.add("loginByCognitoApi", (username, password) => {
  const log = Cypress.log({
    displayName: "COGNITO LOGIN",
    message: [`🔐 Authenticating | ${username}`],
    // @ts-ignore
    autoEnd: false,
  });

  log.snapshot("before");

  const signIn = Auth.signIn({ username, password });

  cy.wrap(signIn, { log: false }).then((cognitoResponse) => {
    const user: CognitoUser = cognitoResponse as CognitoUser;
    const keyPrefixWithUsername = `${user.keyPrefix}.${user.username}`;

    cy.setCookie(
      `${keyPrefixWithUsername}.idToken`,
      user.signInUserSession.idToken.jwtToken
    );

    cy.setCookie(
      `${keyPrefixWithUsername}.accessToken`,
      user.signInUserSession.accessToken.jwtToken
    );

    cy.setCookie(
      `${keyPrefixWithUsername}.refreshToken`,
      user.signInUserSession.refreshToken.token
    );

    cy.setCookie(
      `${keyPrefixWithUsername}.clockDrift`,
      user.signInUserSession.clockDrift
    );

    cy.setCookie(`${user.keyPrefix}.LastAuthUser`, user.username);

    cy.setCookie("amplify-authenticator-authState", "signedIn");
    log.snapshot("after");
    log.end();
  });

  cy.visit("/");
});
