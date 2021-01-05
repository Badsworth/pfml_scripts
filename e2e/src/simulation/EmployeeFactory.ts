import faker from "faker";
import { RandomSSN } from "ssn";
import { EmployeeFactory, EmployerFactory, SimulationClaim } from "./types";

/**
 * Creates an employee "pool" from a previous simulation.
 * @param claims
 */
export function fromClaimData(claims: SimulationClaim[]): EmployeeFactory {
  const pool = [...claims];
  return function (financiallyIneligible: boolean) {
    const claim = shuffle(pool).find(
      (claim) => !!claim.financiallyIneligible === financiallyIneligible
    );
    if (!claim) {
      throw new Error("The employee pool is empty");
    }
    if (
      !(typeof claim.claim.first_name === "string") ||
      !(typeof claim.claim.last_name === "string") ||
      !(typeof claim.claim.tax_identifier === "string") ||
      !(typeof claim.claim.employer_fein === "string")
    ) {
      throw new Error(
        "Claim is missing required properties to extract an employee record."
      );
    }
    // Delete from the pool so we don't reuse it.
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
 * Fisher-Yates algorithm to shuffle array randomly.
 * @see https://bost.ocks.org/mike/shuffle/
 * @param array
 */
function shuffle<T extends unknown[]>(array: T): T {
  let m = array.length;
  let t;
  let i: number;

  // While there remain elements to shuffle…
  while (m) {
    // Pick a remaining element…
    i = Math.floor(Math.random() * m--);

    // And swap it with the current element.
    t = array[m];
    array[m] = array[i];
    array[i] = t;
  }
  return array;
}

export function fromEmployerFactory(
  employerFactory: EmployerFactory
): EmployeeFactory {
  return () => {
    return {
      first_name: faker.name.firstName(),
      last_name: faker.name.lastName(),
      tax_identifier: new RandomSSN().value().toFormattedString(),
      employer_fein: employerFactory().fein,
    };
  };
}
