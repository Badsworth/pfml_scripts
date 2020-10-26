import { EmployeeFactory, SimulationClaim } from "./types";
import faker from "faker";
import employers from "./fixtures/employerPool";
import { RandomSSN } from "ssn";

/**
 * Creates an employee "pool" from a previous simulation.
 * @param claims
 */
export function fromClaimsFactory(claims: SimulationClaim[]): EmployeeFactory {
  const pool = [...claims];
  return function (financiallyIneligible: boolean) {
    const claim = pool.find(
      (claim) => !!claim.financiallyIneligible === financiallyIneligible
    );
    if (!claim) {
      throw new Error("The employee pool is empty");
    }
    // Delete frm the pool so we don't reuse it.
    pool.splice(pool.indexOf(claim), 1);
    return {
      first_name: claim.claim.first_name,
      last_name: claim.claim.last_name,
      tax_identifier: claim.claim.tax_identifier,
      employer_fein: claim.claim.employer_fein,
    };
  };
}

/**
 * Creates brand new, random employees.
 */
export const random: EmployeeFactory = () => {
  return {
    first_name: faker.name.firstName(),
    last_name: faker.name.lastName(),
    tax_identifier: new RandomSSN().value().toFormattedString(),
    employer_fein: employers[Math.floor(Math.random() * employers.length)].fein,
  };
};
