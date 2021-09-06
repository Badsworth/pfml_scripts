/**
 * This file contains typescript overrides for our extra Cypress extensions.
 *
 * @see ./cypress/support/commands.ts
 * @see https://github.com/cypress-io/cypress-realworld-app/tree/develop/cypress
 */
/// <reference types="cypress" />
/// <reference types="cypress-file-upload" />

// Import some types here. We'll reference them below.
type Credentials = import("./src/types").Credentials;
type ApplicationRequestBody = import("./src/api").ApplicationRequestBody;
type ApplicationResponse = import("./src/api").ApplicationResponse;
type waitForClaimDocuments =
  import("./cypress/plugins/DocumentWaiter").default["waitForClaimDocuments"];
type Email = import("./src/submission/TestMailClient").Email;
type GetEmailsOpts = import("./src/submission/TestMailClient").GetEmailsOpts;
type Result = import("pdf-parse").Result;
type DehydratedClaim = import("./src/generation/Claim").DehydratedClaim;
type Employer = import("./src/generation/Employer").Employer;
type EmployerPickSpec = import("./src/generation/Employer").EmployerPickSpec;
type pdf = import("pdf-parse").Result;
type Scenarios = import("./src/types").Scenarios;
type ScenarioSpecs = import("./src/types").ScenarioSpecs;
type APIClaimSpec = import("./src/generation/Claim").APIClaimSpec;
type GeneratedClaim = import("./src/generation/Claim").GeneratedClaim;
type FineosExclusiveLeaveReasons =
  import("./src/generation/Claim").FineosExclusiveLeaveReasons;
type ApplicationSubmissionResponse =
  import("./src/types").ApplicationSubmissionResponse;

declare namespace Cypress {
  interface Cypress {
    // Declare the runner, which is an internal Cypress property.
    // We use it in stash/unstash to grab a unique ID for the run.
    runner: Cypress.Runner;
  }
  interface Chainable<Subject = any> {
    typeMasked(
      text: string,
      options?: Partial<Cypress.TypeOptions>
    ): Chainable<Element>;
    stash(key: string, value: unknown): null;
    unstash<T extends unknown>(key: string): Chainable<T>;
    // Declare our custom tasks.
    stashLog(key: string, value: string | null | undefined): null;
    dependsOnPreviousPass(dependencies?: Mocha.Test[]): null;
    task<T extends Scenarios>(
      event: "generateClaim",
      scenario: T
    ): Chainable<
      ScenarioSpecs[T]["claim"] extends APIClaimSpec
        ? DehydratedClaim
        : GeneratedClaim
    >;
    task(event: "getAuthVerification", mail: string): Chainable<string>;
    task(
      event: "completeSSOLoginFineos",
      credentials?: Credentials
    ): Chainable<string>;
    task(event: "generateCredentials"): Chainable<Credentials>;
    task(event: "getParsedPDF", filename: string): Promise<pdf>;
    task(event: "deleteDownloadFolder", folderName: string): Chainable<true>;
    task(
      event: "getNoticeFileName",
      folderName: string,
      options?: Partial<Cypress.TypeOptions>
    ): Promise<string[]>;

    // Supplying multiple forms of submitClaimToAPI seems to be necessary to provide typing for
    // both forms.
    task(
      event: "submitClaimToAPI",
      arg: DehydratedClaim
    ): Chainable<ApplicationSubmissionResponse>;
    task(event: "submitClaimToAPI", arg: GeneratedClaim): Chainable<never>;
    task(
      event: "submitClaimToAPI",
      arg: DehydratedClaim & {
        credentials?: Credentials;
        employerCredentials?: Credentials;
      }
    ): Chainable<ApplicationSubmissionResponse>;
    task(
      event: "chooseFineosRole",
      arg: {
        /**ID of the account you want to switch the roles for */
        userId: string;
        /**Role preset you want to switch to. */
        preset: FineosSecurityGroups;
      }
    ): Chainable<null>;
    task(event: "pickEmployer", spec: EmployerPickSpec): Chainable<Employer>;
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
