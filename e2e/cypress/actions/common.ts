import type { ConfigFunction } from "../../src/config";

/**
 *
 * @param fieldsetLabel text to identify the fieldset by
 * @param cb callback to be passed into .within() clause inside this function.
 */
export function inFieldsetLabelled(
  fieldsetLabel: string,
  cb: (subject: JQuery<HTMLFieldSetElement>) => void
): void {
  cy.contains("fieldset", fieldsetLabel).within(cb);
}

export const config: ConfigFunction = (name): string => {
  const value = Cypress.env(`E2E_${name}`);
  if (typeof value === "string") {
    return value;
  }
  throw new Error(`Unable to determine config value for ${name}.`);
};
