/**
 * This file contains typescript overrides for our extra Cypress extensions.
 *
 * @see ./cypress/support/commands.ts
 * @see https://github.com/cypress-io/cypress-realworld-app/tree/develop/cypress
 */
/// <reference types="cypress" />
/// <reference types="cypress-file-upload" />

// Import some types here. We'll reference them below.
type Application = import("./src/types").Application;
type Credentials = import("./src/types").Credentials;
type ApplicationRequestBody = import("./src/api").ApplicationRequestBody;

declare namespace Cypress {
  interface Cypress {
    // Declare the runner, which is an internal Cypress property.
    // We use it in stash/unstash to grab a unique ID for the run.
    runner: Cypress.Runner;
  }
  interface cy {}
  interface Chainable<Subject = any> {
    labelled(label: string): Chainable<Element>;
    typeMasked(
      text: string,
      options?: Partial<Cypress.TypeOptions>
    ): Chainable<Element>;
    generateIdVerification<App extends Pick<Application, firstName | lastName>>(
      application: App
    ): Chainable<App & Pick<Application, idVerification>>;
    generateHCPForm<App extends Pick<Application, firstName | lastName>>(
      application: App
    ): Chainable<App & Pick<Application, claim>>;
    stash(key: string, value: unknown): null;
    unstash(key: string): Chainable<unknown>;
    // Declare our custom tasks.
    task(event: "getAuthVerification", mail: string): Chainable<string>;
    task(event: "generateCredentials"): Chainable<Credentials>;
    task(
      event: "submitClaimToAPI",
      options: ApplicationRequestBody
    ): Chainable<string>;
  }
}

// Override @cypress/webpack-preprocess to fix a typing error.
// This is a recurrence of https://github.com/cypress-io/cypress-webpack-preprocessor/issues/76
declare module "@cypress/webpack-preprocessor" {
  namespace CypressWebpackPreProcessor {
    export type Options = { webpackOptions: {} };
    export type FilePreprocessor = (
      file: Cypress.FileObject
    ) => string | Promise<string>;
  }
  const CypressWebpackPreProcessor: (
    options: CypressWebpackPreProcessor.Options
  ) => CypressWebpackPreProcessor.FilePreprocessor;
  export = CypressWebpackPreProcessor;
}

// @see https://www.npmjs.com/package/pdf2json
declare module "pdf2json";
