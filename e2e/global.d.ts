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
type ApplicationResponse = import("./src/api").ApplicationResponse;
type waitForClaimDocuments = import("./cypress/plugins/DocumentWaiter").default["waitForClaimDocuments"];
type Email = import("./cypress/plugins/TestMailClient").Email;
type GetEmailsOpts = import("./cypress/plugins/TestMailClient").GetEmailsOpts;
type Result = import("pdf-parse").Result;
type DehydratedClaim = import("./src/generation/Claim").DehydratedClaim;

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
      scenario: string
    ): Chainable<DehydratedClaim>;

    task(event: "getAuthVerification", mail: string): Chainable<string>;
    task(event: "generateCredentials"): Chainable<Credentials>;
    task(event: "generateLeaveAdminCredentials"): Chainable<Credentials>;
    task(event: "noticeReader", noticeType: string): Chainable<Result>;

    // Supplying multiple forms of submitClaimToAPI seems to be necessary to provide typing for
    // both forms.
    task(event: "submitClaimToAPI", arg: DehydratedClaim): Chainable<ApplicationResponse>;
    task(event: "submitClaimToAPI", arg: DehydratedClaim & {credentials?: Credentials, employerCredentials?: Credentials}): Chainable<ApplicationResponse>;


    task(event: "getEmails", opts: GetEmailsOpts): Chainable<Email[]>;
    task(event: "registerClaimant", options: Credentials): Chainable<true>;
    task(
      event: "registerLeaveAdmin",
      options: Credentials & { fein: string }
    ): Chainable<true>;
    task(
      event: "waitForClaimDocuments",
      waitParams: Parameters<waitForClaimDocuments>[0],
      options?: Partial<Timeoutable & Loggable>
    ): Chainable<boolean>;
  }
}
