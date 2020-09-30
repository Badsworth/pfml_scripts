import * as portal from "./portal";
import * as fineos from "./fineos";
import * as scenarios from "./scenarios";

export { portal, fineos, scenarios };

export function inFieldset(fieldsetLabel: string, cb: () => void): void {
  cy.contains("fieldset", fieldsetLabel).within(cb);
}
