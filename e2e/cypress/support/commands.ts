// ***********************************************
// For more comprehensive examples of custom
// commands please read more here:
// https://on.cypress.io/custom-commands
// ***********************************************s
import "@testing-library/cypress/add-commands";
import {
  trackedResults,
  getRunnableId,
  getRunnableSuiteId,
} from "./dependents";
/**
 * This command types, but masks the input in the logs (eg: for passwords).
 */
Cypress.Commands.add(
  "typeMasked",
  { prevSubject: "element" },
  (subject, chars, options: Partial<Cypress.TypeOptions> = {}) => {
    const opts = { log: true, ...options };
    if (opts.log) {
      Cypress.log({
        $el: subject,
        name: "type",
        message: "*".repeat(chars.length),
      });
    }
    cy.wrap(subject, { log: false }).type(chars, { ...options, log: false });
  }
);

// Simple hash function (see: https://stackoverflow.com/a/8831937)
function simpleHash(string: string) {
  let hash = 0;
  if (string.length == 0) {
    return hash;
  }
  for (let i = 0; i < string.length; i++) {
    const char = string.charCodeAt(i);
    hash = (hash << 5) - hash + char;
    hash = hash & hash; // Convert to 32bit integer
  }
  return hash;
}

// Allows test-crossing state to be saved for consumption later within the same spec.
Cypress.Commands.add("stash", (key: string, data: unknown) => {
  // Formulate filename based on runner start time and test name.
  // Even if our runner window reloads and we lose all variables set there, these things stay the same.
  const runId = Cypress.runner.getStartTime();
  const testId = Cypress.spec.name;
  const hash = simpleHash(`${runId}-${testId}`);
  Cypress.log({
    name: "stash",
    message: key,
    consoleProps() {
      return {
        hash: hash,
        key: key,
        value: data,
      };
    },
  });
  cy.writeFile(`/tmp/${hash}/${key}`, JSON.stringify(data), { log: false });
});

// Allows test-crossing state to be read after being written within the same spec.
Cypress.Commands.add("unstash", (key: string) => {
  const runId = Cypress.runner.getStartTime();
  const testId = Cypress.spec.name;
  const hash = simpleHash(`${runId}-${testId}`);

  return (
    cy
      // Short timeout because by definition this file has to exist before unstash is called.
      .readFile(`/tmp/${hash}/${key}`, { log: false, timeout: 1000 })
      .then(function (contents) {
        const data = JSON.parse(contents);
        Cypress.log({
          name: "unstash",
          message: key,
          consoleProps() {
            return {
              hash: hash,
              key: key,
              data: data,
            };
          },
        });
        return data;
      })
  );
});

Cypress.Commands.add(
  "stashLog",
  (key: string, data: string | null | undefined) => {
    if (!data) {
      throw new Error("Cannot stash undefined data");
    }
    cy.stash(key, data);
    cy.log(data);
  }
);

/**
 * Return the current tests attempt count
 * This is helpful in situations where a test timed out on the very final step, but the action eventually completed sucessfully (i.e: Claim Approval)
 */
Cypress.Commands.add("tryCount", () => {
  // @ts-ignore
  const runnable = cy.state("runnable") as Runnable;
  const thisSuiteResults = trackedResults[getRunnableSuiteId(runnable)];
  const thisTestId = getRunnableId(runnable);
  if (!thisSuiteResults) return cy.wrap(0);
  if (!thisSuiteResults[thisTestId]) return cy.wrap(0);
  if (thisSuiteResults[thisTestId].attempts === undefined) return cy.wrap(0);
  return cy.wrap(thisSuiteResults[thisTestId].attempts as number);
});
