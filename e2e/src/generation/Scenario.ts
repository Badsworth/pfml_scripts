import { EmployeePickSpec } from "./Employee";
import { ClaimSpecification } from "./Claim";

export type ScenarioSpecification = {
  employee: EmployeePickSpec;
  claim: ClaimSpecification;
};
