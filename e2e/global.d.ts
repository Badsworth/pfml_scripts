/**
 * This file contains typescript overrides for our extra Cypress extensions.
 *
 * @see ./cypress/support/commands.ts
 * @see https://github.com/cypress-io/cypress-realworld-app/tree/develop/cypress
 */
/// <reference types="cypress" />
/// <reference types="cypress-file-upload" />

// Import some types here. We'll reference them below.
type Application = import('./src/types').Application;
type FillPDFTaskOptions = import('./cypress/plugins/index').FillPDFTaskOptions

declare namespace Cypress {
    interface Cypress {
      // Declare the runner, which is an internal Cypress property.
      // We use it in stash/unstash to grab a unique ID for the run.
      runner: Cypress.Runner
    }
    interface cy {

    }
    interface Chainable<Subject = any> {
        labelled(label: string): Chainable<Element>;
        typeMasked(text: string, options?: Partial<Cypress.TypeOptions>): Chainable<Element>
        generateIdVerification<App extends Pick<Application, firstName|lastName>>(application: App): Chainable<App & Pick<Application, idVerification>>
        generateHCPForm<App extends Pick<Application, firstName|lastName>>(application: App): Chainable<App & Pick<Application, claim>>
        stash(key: string, value: unknown): null
        unstash(key: string): Chainable<unknown>

        // Declare our custom tasks.
        task(event: "getAuthVerification", mail: string): Chainable<string>;
        task(event: "fillPDF", options: FillPDFTaskOptions): Chainable<string>;

    }

}
