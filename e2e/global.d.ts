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
type SimulationClaim = import("./src/simulation/types").SimulationClaim;
type ApplicationRequestBody = import("./src/api").ApplicationRequestBody;
type waitForClaimDocuments = import("./cypress/plugins/DocumentWaiter").default["waitForClaimDocuments"];
type Email = import("./cypress/plugins/TestMailClient").Email;
type GetEmailsOpts = import("./cypress/plugins/TestMailClient").GetEmailsOpts;
type Result = import("pdf-parse").Result;

declare namespace Cypress {
  interface Cypress {
    // Declare the runner, which is an internal Cypress property.
    // We use it in stash/unstash to grab a unique ID for the run.
    runner: Cypress.Runner;
  }
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
    unstash<T extends unknown>(key: string): Chainable<T>;
    // Declare our custom tasks.
    stashLog(key: string, value: string | null | undefined): null;
    task(
      event: "generateClaim",
      { claimType: string, employeeType: string }
    ): Chainable<SimulationClaim>;

    task(event: "getAuthVerification", mail: string): Chainable<string>;
    task(
      event: "generateCredentials",
      isEmployer: boolean
    ): Chainable<Credentials>;
    task(event: "noticeReader", noticeType: string): Chainable<Result>;
    task(
      event: "submitClaimToAPI",
      options: SimulationClaim
    ): Chainable<PartialResponse>;
    task(event: "getEmails", opts: GetEmailsOpts): Chainable<Email[]>;
    task(event: "registerClaimant", options: Credentials): Chainable<true>;
    task(
      event: "registerLeaveAdmin",
      options: Credentials & { fein: string }
    ): Chainable<true>;
    task(
      event: "waitForClaimDocuments",
      options: Parameters<waitForClaimDocuments>[0]
    ): Chainable<boolean>;
  }
}
