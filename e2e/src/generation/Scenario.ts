import { EmployeePickSpec } from "./Employee";
import { ClaimSpecification } from "./Claim";

/**
 * Describes a particular scenario.
 *
 * Consists of information about how the claim should be generated, including information about the employee
 * that should be used.
 */
export type ScenarioSpecification = {
  employee: EmployeePickSpec;
  claim: ClaimSpecification;
};
