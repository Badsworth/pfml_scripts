import * as portal from "./portal";
import * as fineos from "./fineos";

export { portal, fineos };

export function inFieldset(fieldsetLabel: string, cb: () => void): void {
  cy.contains("fieldset", fieldsetLabel).within(cb);
}
