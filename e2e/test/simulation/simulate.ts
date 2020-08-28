import { describe, it, expect, jest } from "@jest/globals";
import { scenario, chance } from "../../src/simulation/simulate";
import employerPool from "../../src/simulation/fixtures/employerPool";
import type { SimulationClaim } from "@/simulation/types";
import {
  generateHCP,
  generateIDBack,
  generateIDFront,
} from "../../src/simulation/documents";

jest.mock("../../src/simulation/documents");

const opts = {
  documentDirectory: "/tmp",
};

describe("Simulation Generator", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("Should have claim properties", async () => {
    const claim = await scenario({ residence: "MA-proofed" })(opts);
    expect(claim.claim).toMatchObject({
      employment_status: "Employed",
      first_name: expect.any(String),
      last_name: expect.any(String),
      employee_ssn: expect.stringMatching(/\d{3}-\d{2}-\d{4}/),
      date_of_birth: expect.stringMatching(/\d{4}-\d{2}-\d{2}/),
    });
  });

  it("Should pull an employer from the pool", async () => {
    const employerFeins = employerPool.map((e) => e.fein);
    const claim = await scenario({ residence: "MA-proofed" })(opts);
    expect(employerFeins).toContain(claim.claim.employer_fein);
  });

  it("Should populate the mass_id property for mass proofed claims", async () => {
    const claim = await scenario({ residence: "MA-proofed" })(opts);
    expect(claim.claim.mass_id).toBeTruthy();
    expect(claim.claim.has_state_id).toBe(true);
  });

  it("Should populate the mass_id property for mass unproofed claims", async () => {
    const claim = await scenario({ residence: "MA-unproofed" })(opts);
    expect(claim.claim.mass_id).toBeTruthy();
    expect(claim.claim.has_state_id).toBe(true);
  });

  it("Should not populate the mass_id property for OOS claims", async () => {
    const claim = await scenario({ residence: "OOS" })(opts);
    expect(claim.claim.mass_id).toBe(null);
    expect(claim.claim.has_state_id).toBe(false);
  });

  it("Should default to generating financially eligible claims", async () => {
    const claim = await scenario({ residence: "OOS" })(opts);
    expect(claim.financiallyIneligible).toBe(false);
  });

  it("Should populate financial eligibility field.", async () => {
    const claim = await scenario({
      residence: "OOS",
      financiallyIneligible: true,
    })(opts);
    expect(claim.financiallyIneligible).toBe(true);
  });

  it("Should generate an HCP form", async () => {
    const claim = await scenario({
      residence: "OOS",
    })(opts);

    expect(generateHCP).toHaveBeenCalledWith(
      claim.claim,
      expect.stringMatching(/^\/tmp\/[\d-]+\.hcp\.pdf/)
    );
  });
  it("Should generate an License Front", async () => {
    const claim = await scenario({
      residence: "OOS",
    })(opts);

    expect(generateIDFront).toHaveBeenCalledWith(
      claim.claim,
      expect.stringMatching(/^\/tmp\/[\d-]+\.id-front\.pdf/)
    );
  });

  it("Should generate a license back", async () => {
    const claim = await scenario({
      residence: "OOS",
    })(opts);
    expect(generateIDBack).toHaveBeenCalledWith(
      claim.claim,
      expect.stringMatching(/^\/tmp\/[\d-]+\.id-back\.pdf/)
    );
  });
});

describe("Chance Simulation Generator", () => {
  it("Should generate according to probability", async () => {
    const first = {} as SimulationClaim;
    const second = {} as SimulationClaim;

    const generator = chance([
      [1, () => Promise.resolve(first)],
      [3, () => Promise.resolve(second)],
    ]);

    const counts = [0, 0];
    for (let i = 0; i < 100; i++) {
      const x = await generator(opts);
      if (x === first) {
        counts[0]++;
      } else if (x === second) {
        counts[1]++;
      } else {
        throw new Error("Invalid submission returned.");
      }
    }
    expect(counts[0]).toBeLessThan(counts[1]);
  });
});
