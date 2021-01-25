import faker from "faker";
import { RandomSSN } from "ssn";
import {
  EmployeeFactory,
  EmployerFactory,
  SimulationClaim,
  WageSpecification,
} from "./types";
import unique from "./unique";

/**
 * Creates an employee "pool" from a previous simulation.
 * @param claims
 */
export function fromClaimData(claims: SimulationClaim[]): EmployeeFactory {
  const pool = [...claims].map((claim) => {
    // Backward compatibility - generate wage data for any claims built without the wages prop.
    return {
      ...claim,
      wages: claim.wages ?? (claim.financiallyIneligible ? 4800 : 6000),
    };
  });
  return function (wageSpec) {
    const claim = shuffle(pool).find((claim) =>
      wagesInBounds(claim.wages, wageSpec)
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
      wages: claim.wages,
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

function wagesInBounds(wages: number, spec: WageSpecification) {
  const [min, max] = getWageBounds(spec);
  return wages >= min && wages <= max;
}

// Generate the min/max bounds for yearly wages.
function getWageBounds(spec: WageSpecification) {
  if (typeof spec === "number") {
    return [spec, spec];
  }
  switch (spec) {
    case "ineligible":
      return [2000, 5399];
    case "eligible":
      return [5400, 100000];
    case "high":
      return [90000, 100000];
    case "medium":
      return [30000, 90000];
    case "low":
      return [5400, 30000];
    default:
      throw new Error(`Invalid wage specification: ${spec}`);
  }
}
// Generate a yearly wage amount, given a specification.
function generateWages(spec: WageSpecification): number {
  if (typeof spec === "number") {
    return spec;
  }
  const [min, max] = getWageBounds(spec);
  return faker.random.number({ min, max });
}

const generateSSN = unique(() => {
  let ssn;
  do {
    ssn = new RandomSSN().value().toFormattedString();
  } while (ssn.startsWith("250-0"));
  return ssn;
});

export function fromEmployerFactory(
  employerFactory: EmployerFactory
): EmployeeFactory {
  return (wageSpec) => {
    return {
      first_name: faker.name.firstName(),
      last_name: faker.name.lastName(),
      tax_identifier: generateSSN(),
      employer_fein: employerFactory().fein,
      wages: generateWages(wageSpec),
    };
  };
}

/**
 * Combine multiple factories into one. This is useful if, for example, you want to try
 * an existing employee pool and fall back to random generation.
 *
 * The factories will be tried for each claim in order, so the first factory will always have preference if it is
 * able to return a match.
 */
export const fromMultipleFactories = (
  ...factories: EmployeeFactory[]
): EmployeeFactory => {
  return (wageSpec) => {
    for (const factory of factories) {
      try {
        return factory(wageSpec);
      } catch (e) {
        // Just move onto the next factory if we hit an error with the first.
      }
    }
    throw new Error(
      "Unable to find or generate an employee using any of the provided factories"
    );
  };
};
