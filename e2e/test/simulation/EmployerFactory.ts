import { describe, it, expect } from "@jest/globals";
import employerPool from "../../src/simulation/fixtures/employerPool";
import { EmployerFactory } from "../../src/simulation/types";
import {
  randomEmployer,
  fromEmployersFactory,
} from "../../src/simulation/EmployerFactory";

describe("Employer random generator", () => {
  it("Should generate a random employer", () => {
    const employer = randomEmployer();
    expect(employer.fein).toMatch(/[\d]{2}-[\d]{7}$/g);
  });
});

describe("Employer pool generator", () => {
  let pool: EmployerFactory;

  beforeEach(() => {
    pool = fromEmployersFactory(employerPool);
  });

  it("Should pull an employer from the employer pool", () => {
    const employer = pool();
    expect(employerPool).toContainEqual(expect.objectContaining(employer));
  });
});
