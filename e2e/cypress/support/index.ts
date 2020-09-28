// ***********************************************************
// This example support/index.js is processed and
// loaded automatically before your test files.
//
// This is a great place to put global configuration and
// behavior that modifies Cypress.
//
// You can change the location of this file or turn off
// automatically serving support files with the
// 'supportFile' configuration option.
//
// You can read more here:
// https://on.cypress.io/configuration
// ***********************************************************

// Import commands.js using ES2015 syntax:
import "./commands";
import "cypress-file-upload";
import "@rckeller/cypress-unfetch";
import "@rckeller/cypress-unfetch/await";

// Suppress a particular error message that is causing immediate failure due to a JS
// error on the client side.
Cypress.on("uncaught:exception", (e) => {
  // Suppress failures due to this error, which we can't do anything about.
  if (e.message.indexOf(`Cannot set property 'status' of undefined`)) {
    return false;
  }
});

afterEach(() => {
  cy.await();
});
