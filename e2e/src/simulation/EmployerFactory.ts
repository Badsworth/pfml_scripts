import faker from "faker";
import unique from "./unique";
import { EmployerFactory, Employer } from "./types";

/**
 * Creates an employer "pool" from employer data.
 * @param employers
 */
export function fromEmployerData(employers: Employer[]): EmployerFactory {
  // Roulette wheel containing employers. Controls the probability of returning
  // an employer of a particular size.
  const wheel = employers.reduce((slots, employer, i) => {
    switch (employer.size) {
      case "large":
        // Large employers = 10x more employees than a small employer.
        return slots.concat(new Array(10).fill(i));
      case "medium":
        // Medium employers = 3x more employees than a small employer.
        return slots.concat(new Array(3).fill(i));
      default:
        // Also applies to "small" employers.
        return slots.concat([i]);
    }
  }, [] as number[]);

  return function () {
    const i = wheel[Math.floor(Math.random() * wheel.length)];
    return employers[i];
  };
}

const makeAccountKey = unique(() =>
  faker.helpers.replaceSymbolWithNumber("###########")
);
const makeCompanyName = unique(
  () =>
    `${faker.company
      .bs()
      .replace(/(^|\s|-)\w/g, (char) =>
        char.toUpperCase()
      )} ${faker.company.companySuffix()}`
);
const makeFEIN = unique(() =>
  faker.helpers.replaceSymbolWithNumber("##-#######")
);

/**
 * Creates brand new, random employers.
 */
export const randomEmployer: EmployerFactory = () => {
  return {
    accountKey: makeAccountKey(),
    name: makeCompanyName(),
    fein: makeFEIN(),
    street: faker.address.streetAddress(),
    city: faker.address.city(),
    state: "MA",
    zip: faker.address.zipCode("#####-####"),
    dba: "",
    family_exemption: false,
    medical_exemption: false,
    updated_date: new Date(),
    size: makeEmployerSize(),
  } as Employer;
};

// Roulette wheel algorithm.
// Will generate 50x small employers and 10x medium employers for every large employer.
const employerSizeWheel = [
  ...new Array(50).fill("small"),
  ...new Array(10).fill("medium"),
  ...new Array(1).fill("large"),
];
function makeEmployerSize(): "small" | "medium" | "large" {
  return employerSizeWheel[
    Math.floor(Math.random() * employerSizeWheel.length)
  ];
}
