import { Application } from "../types";

export default class LoginPage {
  visit(): this {
    cy.visit("/");
    return this;
  }
  register(application: Pick<Application, "email" | "password">): this {
    cy.visit("/");
    cy.contains("a", "create an account").click();
    cy.labelled("Email address").type(application.email);
    cy.labelled("Password").type(application.password);
    cy.contains("button", "Create account").click();
    cy.task("getAuthVerification", application.email).then((code: string) => {
      cy.labelled("6-digit code").type(code as string);
      cy.contains("button", "Submit").click();
    });
    return this;
  }
  login(application: Pick<Application, "email" | "password">): this {
    cy.visit("/");
    cy.get('[data-test="username-input"]').type(application.email);
    cy.get('[data-test="sign-in-password-input"]').typeMasked(
      application.password
    );
    cy.get('[data-test="sign-in-sign-in-button"]').click();
    return this;
  }
}
