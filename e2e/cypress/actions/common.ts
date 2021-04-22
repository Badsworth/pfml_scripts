export function inFieldset(fieldsetLabel: string, cb: () => void): void {
  cy.contains("fieldset", fieldsetLabel).within(cb);
}
