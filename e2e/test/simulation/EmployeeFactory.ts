import {
  fromEmployerFactory,
  fromClaimData,
} from "../../src/simulation/EmployeeFactory";
import { ParseSSN } from "ssn";
import { describe, it, expect } from "@jest/globals";
import { EmployeeFactory } from "../../src/simulation/types";

const employerFactory = () => ({
  accountKey: "12345678910",
  name: "Wayne Enterprises",
  fein: "84-7847847",
  street: "1 Wayne Tower",
  city: "Gotham City",
  state: "MA",
  zip: "01010-1234",
  dba: "",
  family_exemption: false,
  medical_exemption: false,
});

describe("Random generator", () => {
  it("Should generate an employee with a valid SSN", () => {
    const employee = fromEmployerFactory(employerFactory)(false);
    new ParseSSN((employee.tax_identifier ?? "").replace(/-/g, ""));
  });

  it("Should pull an employer from the employer pool", () => {
    const employee = fromEmployerFactory(employerFactory)(false);
    expect(employee.employer_fein).toEqual("84-7847847");
  });
});

describe("Employee pool generator", () => {
  let pool: EmployeeFactory;
  const claimA = {
    id: "123",
    claim: {
      first_name: "John",
      last_name: "Doe",
      tax_identifier: "000-00-0000",
      employer_fein: "99-999999",
    },
    scenario: "TEST",
    documents: [],
    paymentPreference: {},
    financiallyIneligible: false,
  };
  const claimB = {
    id: "123",
    claim: {
      first_name: "Dave",
      last_name: "Doe",
      tax_identifier: "123-00-0000",
      employer_fein: "99-999999",
    },
    scenario: "TEST",
    documents: [],
    paymentPreference: {},
    financiallyIneligible: true,
  };

  beforeEach(() => {
    pool = fromClaimData([claimA, claimB]);
  });

  it("Should pull an employee from the pool", () => {
    expect(pool(false)).toMatchObject({
      tax_identifier: claimA.claim.tax_identifier,
    });
  });

  it("Should pull a financially ineligible employee from the pool", () => {
    expect(pool(true)).toMatchObject({
      tax_identifier: claimB.claim.tax_identifier,
    });
  });

  it("Should exhaust the pool", () => {
    pool(false);
    expect(() => pool(false)).toThrow("The employee pool is empty");
  });
});
