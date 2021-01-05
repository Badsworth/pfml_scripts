import { describe, it, expect } from "@jest/globals";
import { EmployerFactory } from "../../src/simulation/types";
import {
  randomEmployer,
  fromEmployerData,
} from "../../src/simulation/EmployerFactory";
import employers from "../../employers/e2e.json";

describe("Employer random generator", () => {
  it("Should generate a random employer", () => {
    const employer = randomEmployer();
    expect(employer.fein).toMatch(/[\d]{2}-[\d]{7}$/g);
  });
});

describe("Employer pool generator", () => {
  let pool: EmployerFactory;

  beforeEach(() => {
    pool = fromEmployerData(employers);
  });

  it("Should pull an employer from the employer pool", () => {
    const employer = pool();
    expect(employers).toContainEqual(expect.objectContaining(employer));
  });
});
