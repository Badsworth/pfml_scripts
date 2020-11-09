import faker from "faker";
import { EmployerFactory, Employer } from "./types";

/**
 * Creates an employer "pool" from a previous simulation.
 * @param employers
 */
export function fromEmployersFactory(employers: Employer[]): EmployerFactory {
  return function () {
    return employers[Math.floor(Math.random() * employers.length)];
  };
}

/**
 * Creates brand new, random employers.
 */
export const randomEmployer: EmployerFactory = () => {
  return {
    accountKey: faker.helpers.replaceSymbolWithNumber("##########"),
    name: faker.company.companyName(0),
    fein: faker.helpers.replaceSymbolWithNumber("##-#######"),
    street: faker.address.streetAddress(),
    city: faker.address.city(),
    state: "MA",
    zip: faker.address.zipCode(),
    dba: "",
    family_exemption: false,
    medical_exemption: false,
    updated_date: new Date(),
  } as Employer;
};
