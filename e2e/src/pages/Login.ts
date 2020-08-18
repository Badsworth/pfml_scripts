import { Application } from "../types";

export default class LoginPage {
  visit(): this {
    cy.visit("/");
    return this;
  }
  registerAccount(application: Pick<Application, "email" | "password">): this {
    cy.visit("/");
    cy.contains("a", "create an account").click();
    cy.labelled("Email address").type(application.email);
    cy.labelled("Password").type(application.password);
    cy.contains("button", "Create account").click();
    return this;
  }
  verifyAccount(application: Pick<Application, "email" | "password">): this {
    cy.task("getAuthVerification", application.email).then((code: string) => {
      cy.labelled("6-digit code").type(code as string);
      cy.contains("button", "Submit").click();
    });
    return this;
  }
  login(application: Pick<Application, "email" | "password">): this {
    cy.visit("/");
    cy.labelled("Email address").type(application.email);
    cy.labelled("Password").typeMasked(application.password);
    cy.contains("button", "Log in").click();
    return this;
  }
}
