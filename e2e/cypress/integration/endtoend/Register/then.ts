import { Then } from "cypress-cucumber-preprocessor/steps";
import { LoginPage } from "@/pages";

Then("I should be able to register a new account", function () {
  new LoginPage().verifyAccount(this.application);
});
