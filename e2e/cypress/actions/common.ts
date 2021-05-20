import type { ConfigFunction } from "../../src/config";

export function inFieldset(fieldsetLabel: string, cb: () => void): void {
  cy.contains("fieldset", fieldsetLabel).within(cb);
}

export const config: ConfigFunction = (name): string => {
  const value = Cypress.env(`E2E_${name}`);
  if (typeof value === "string") {
    return value;
  }
  throw new Error(`Unable to determine config value for ${name}.`);
};
