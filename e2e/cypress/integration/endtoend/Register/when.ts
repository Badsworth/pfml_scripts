import { When } from "cypress-cucumber-preprocessor/steps";
import { LoginPage } from "@/pages";

When("I submit the account registration form", function () {
  new LoginPage().registerAccount(this.application);
});
