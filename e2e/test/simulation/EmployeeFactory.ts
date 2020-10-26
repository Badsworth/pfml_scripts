import employers from "../../src/simulation/fixtures/employerPool";
import {
  random,
  fromClaimsFactory,
} from "../../src/simulation/EmployeeFactory";
import { ParseSSN } from "ssn";
import { describe, it, expect } from "@jest/globals";
import { EmployeeFactory } from "../../src/simulation/types";

describe("Random generator", () => {
  it("Should generate an employee with a valid SSN", () => {
    const employee = random(false);
    new ParseSSN((employee.tax_identifier ?? "").replace(/-/g, ""));
  });

  it("Should pull an employer from the employer pool", () => {
    const employee = random(false);
    expect(employers.map((e) => e.fein)).toContain(employee.employer_fein);
  });
});

describe("Employee pool generator", () => {
  let pool: EmployeeFactory;
  const claimA = {
    claim: {
      first_name: "John",
      last_name: "Doe",
      tax_identifier: "000-00-0000",
      employer_fein: "99-999999",
    },
    scenario: "TEST",
    documents: [],
    financiallyIneligible: false,
  };
  const claimB = {
    claim: {
      first_name: "Dave",
      last_name: "Doe",
      tax_identifier: "123-00-0000",
      employer_fein: "99-999999",
    },
    scenario: "TEST",
    documents: [],
    financiallyIneligible: true,
  };

  beforeEach(() => {
    pool = fromClaimsFactory([claimA, claimB]);
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
