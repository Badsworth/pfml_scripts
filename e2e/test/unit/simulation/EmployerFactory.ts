import { describe, it, expect } from "@jest/globals";
import { EmployerFactory, Employer } from "../../../src/simulation/types";
import {
  randomEmployer,
  fromEmployerData,
} from "../../../src/simulation/EmployerFactory";
import employers from "../../../employers/e2e.json";

describe("Employer random generator", () => {
  it("Should generate a random employer", () => {
    const employer = randomEmployer();
    expect(employer.fein).toMatch(/[\d]{2}-[\d]{7}$/g);
  });

  it("Should generate employers with the correct size distribution", () => {
    const counts = new Map<Employer["size"], number>();
    for (let i = 0; i < 10000; i++) {
      const size = randomEmployer().size;
      counts.set(size, (counts.get(size) ?? 0) + 1);
    }
    expect(counts.get("small")).toBeGreaterThan(counts.get("medium") ?? 0);
    expect(counts.get("medium")).toBeGreaterThan(counts.get("large") ?? 0);
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

  it("Should pull an employer from the pool according to employer size", () => {
    const counts = new Map<Employer, number>();
    const employer1 = { ...employers[0], size: "small" as const };
    const employer2 = { ...employers[1], size: "medium" as const };
    const employer3 = { ...employers[1], size: "large" as const };

    pool = fromEmployerData([employer1, employer2, employer3]);
    for (let i = 0; i < 10000; i++) {
      const employer = pool();
      counts.set(employer, (counts.get(employer) ?? 0) + 1);
    }
    expect(counts.get(employer1)).toBeLessThan(counts.get(employer2) ?? 0);
    expect(counts.get(employer2)).toBeLessThan(counts.get(employer3) ?? 0);
  });
});
