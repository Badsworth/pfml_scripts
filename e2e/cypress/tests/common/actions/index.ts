import * as portal from "./portal";
import * as fineos from "./fineos";
import * as email from "./email";

export { portal, fineos, email };

export function inFieldset(fieldsetLabel: string, cb: () => void): void {
  cy.contains("fieldset", fieldsetLabel).within(cb);
}
