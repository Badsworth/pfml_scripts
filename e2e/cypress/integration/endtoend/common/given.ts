import { Given } from "cypress-cucumber-preprocessor/steps";
import { LoginPage } from "@/pages";

Given("I am an anonymous user on the portal homepage", () =>
  new LoginPage().visit()
);
