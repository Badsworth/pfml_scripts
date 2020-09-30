import { ScenarioClaimTestTypes } from "@/types";
import { defineParameterType } from "cypress-cucumber-preprocessor/steps";

defineParameterType({
  name: "testType",
  regexp: new RegExp(ScenarioClaimTestTypes.join("|")),
  transformer: (s) => s,
});
