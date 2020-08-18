import { MedicalClaimTestTypes } from "@/types";
import { defineParameterType } from "cypress-cucumber-preprocessor/steps";

defineParameterType({
  name: "testType",
  regexp: new RegExp(MedicalClaimTestTypes.join("|")),
  transformer: (s) => s,
});
