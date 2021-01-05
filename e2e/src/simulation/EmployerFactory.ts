import faker from "faker";
import unique from "./unique";
import { EmployerFactory, Employer } from "./types";

/**
 * Creates an employer "pool" from a previous simulation.
 * @param employers
 */
export function fromEmployerData(employers: Employer[]): EmployerFactory {
  return function () {
    return employers[Math.floor(Math.random() * employers.length)];
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
  } as Employer;
};
