// ***********************************************
// For more comprehensive examples of custom
// commands please read more here:
// https://on.cypress.io/custom-commands
// ***********************************************

import { Application } from "../../src/types";

/**
 * This command selects an input by the HTML label "for" value.
 */
Cypress.Commands.add("labelled", (label: string) => {
  return cy.contains("label", label, { matchCase: false }).and(($el) => {
    const labelFor = $el.attr("for");
    if (!labelFor || labelFor.length < 1) {
      throw new Error(
        `Unable to find for attribute on label. Got: ${labelFor}`
      );
    }
    // Use Cypress.$ because cy.get seems to be scoped to the label.
    // Also, escape "(" and ")" in the selector. Fineos uses these in some of its IDs, and Cypress
    // does not like them.
    return Cypress.$(`#${labelFor.replace(/(?<!\\)([()])/g, "\\$1")}`);
  });
});

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
    return cy
      .wrap(subject, { log: false })
      .type(chars, { ...options, log: false });
  }
);

/**
 * This command populates the idVerification portion of an application with a PDF version of a license.
 *
 * This command will generate the PDF files on the fly.
 */
Cypress.Commands.add(
  "generateIdVerification",
  (application: Pick<Application, "firstName" | "lastName">) => {
    const fillData = {
      "Given Name Text Box": application.firstName,
      "Family Name Text Box": application.lastName,
    };
    return cy
      .task("fillPDF", { source: "form.pdf", data: fillData })
      .then((front) => {
        return cy
          .task("fillPDF", { source: "form.pdf", data: fillData })
          .then((back) => {
            return {
              ...application,
              idVerification: {
                front: {
                  fileContent: Cypress.Blob.binaryStringToBlob(
                    (front as unknown) as string
                  ),
                  fileName: "id.front.pdf",
                  mimeType: "application/pdf",
                  encoding: "utf-8",
                },
                back: {
                  fileContent: Cypress.Blob.binaryStringToBlob(
                    (back as unknown) as string
                  ),
                  fileName: "id.back.pdf",
                  mimeType: "application/pdf",
                  encoding: "utf-8",
                },
              },
            };
          });
      });
  }
);

/**
 * Adds a generated HCP form to the application.
 *
 * The HCP form will be a generated PDF file.
 */
Cypress.Commands.add("generateHCPForm", (application: Application) => {
  const fillData = {
    "Given Name Text Box": application.firstName,
    "Family Name Text Box": application.lastName,
  };
  return cy
    .task("fillPDF", { source: "form.pdf", data: fillData })
    .then((providerForm) => {
      return {
        ...application,
        claim: {
          ...application.claim,
          providerForm: {
            fileContent: Cypress.Blob.binaryStringToBlob(
              (providerForm as unknown) as string
            ),
            fileName: "hcp.pdf",
            mimeType: "application/pdf",
            encoding: "utf-8",
          },
        },
      };
    });
});

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

  return cy
    .readFile(`/tmp/${hash}/${key}`, { log: false })
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
    });
});
