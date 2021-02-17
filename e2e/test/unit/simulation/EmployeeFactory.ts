import {
  fromMultipleFactories,
  fromEmployerFactory,
  fromClaimData,
} from "../../../src/simulation/EmployeeFactory";
import { ParseSSN } from "ssn";
import { describe, it, expect, jest } from "@jest/globals";
import { EmployeeFactory } from "../../../src/simulation/types";

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
  wages: 4000,
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
  wages: 10000,
};
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
    const employee = fromEmployerFactory(employerFactory)("eligible");
    new ParseSSN((employee.tax_identifier ?? "").replace(/-/g, ""));
  });

  it("Should pull an employer from the employer pool", () => {
    const employee = fromEmployerFactory(employerFactory)("eligible");
    expect(employee.employer_fein).toEqual("84-7847847");
  });

  const cases = [
    ["ineligible" as const, 2000, 5399],
    ["eligible" as const, 5400, 100000],
  ];
  cases.forEach(([spec, min, max]) => {
    it(`Should generate wage data according to spec: ${spec}`, () => {
      const employee = fromEmployerFactory(employerFactory)(spec);
      expect(employee.wages).toBeGreaterThanOrEqual(min as number);
      expect(employee.wages).toBeLessThanOrEqual(max as number);
    });
  });

  it("Should generate a specific wage amount if given one", () => {
    const employee = fromEmployerFactory(employerFactory)(100);
    expect(employee.wages).toEqual(100);
  });
});

describe("Employee pool generator", () => {
  let pool: EmployeeFactory;

  beforeEach(() => {
    pool = fromClaimData([claimA, claimB]);
  });

  it("Should pull an ineligible employee from the pool", () => {
    expect(pool("ineligible")).toMatchObject({
      tax_identifier: claimA.claim.tax_identifier,
    });
  });

  it("Should pull a financially eligible employee from the pool", () => {
    expect(pool("eligible")).toMatchObject({
      tax_identifier: claimB.claim.tax_identifier,
    });
  });

  it("Should exhaust the pool", () => {
    pool("ineligible");
    expect(() => pool("ineligible")).toThrow("The employee pool is empty");
  });

  it("Should be usable, even with legacy claims", () => {
    const ineligibleClaim = {
      ...claimB,
      wages: undefined,
      financiallyIneligible: true,
    };
    const eligibleClaim = { ...claimB, wages: undefined };
    const pool = fromClaimData([ineligibleClaim, eligibleClaim]);
    expect(pool("ineligible")).toMatchObject({
      tax_identifier: ineligibleClaim.claim.tax_identifier,
    });
    expect(pool("eligible")).toMatchObject({
      tax_identifier: eligibleClaim.claim.tax_identifier,
    });
  });
});

describe("Chain Generator", () => {
  const gen1 = jest.fn(fromClaimData([claimA]));
  const gen2 = jest.fn(fromClaimData([claimB]));
  const pool = fromMultipleFactories(gen1, gen2);

  beforeEach(() => {
    jest.resetAllMocks();
  });

  it("Should invoke the first factory first", () => {
    pool("eligible");
    expect(gen1).toHaveBeenCalledTimes(1);
    expect(gen2).not.toHaveBeenCalled();
  });

  it("Should try the second factory when the first one fails.", () => {
    gen1.mockImplementation(() => {
      throw new Error("Test");
    });
    pool("eligible");
    expect(gen1).toHaveBeenCalledTimes(1);
    expect(gen2).toHaveBeenCalledTimes(1);
  });

  it("Should error out when no factory matches", () => {
    gen1.mockImplementation(() => {
      throw new Error("Test");
    });
    gen2.mockImplementation(() => {
      throw new Error("Test");
    });
    expect(() => pool("eligible")).toThrowError(
      "Unable to find or generate an employee using any of the provided factories"
    );
  });
});
