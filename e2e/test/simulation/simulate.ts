import { describe, it, expect, jest } from "@jest/globals";
import { scenario, chance, ScenarioOpts } from "../../src/simulation/simulate";
import employerPool from "../../src/simulation/fixtures/employerPool";
import type { SimulationClaim } from "@/simulation/types";
import generators from "../../src/simulation/documents";
import { ParseSSN } from "ssn";
import fs from "fs";

jest.mock("../../src/simulation/documents");

const opts = {
  documentDirectory: "/tmp",
};

const medical: ScenarioOpts = {
  residence: "MA-proofed",
  reason: "Serious Health Condition - Employee",
  docs: {
    HCP: {},
    MASSID: {},
  },
};
const bonding: ScenarioOpts = {
  residence: "MA-proofed",
  reason: "Child Bonding",
  reason_qualifier: "Newborn",
  bondingDate: "past",
  docs: {
    HCP: {},
    MASSID: {},
  },
};

describe("Simulation Generator", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("Should have claim properties", async () => {
    const claim = await scenario("TEST", medical)(opts);
    expect(claim.scenario).toEqual("TEST");
    expect(claim.claim).toMatchObject({
      employment_status: "Employed",
      first_name: expect.any(String),
      last_name: expect.any(String),
      tax_identifier: expect.stringMatching(/\d{3}-\d{2}-\d{4}/),
      date_of_birth: expect.stringMatching(/\d{4}-\d{2}-\d{2}/),
    });
  });

  it("Should have payment information", async () => {
    const claim = await scenario("TEST", medical)(opts);
    const { payment_preferences } = claim.claim;
    expect(payment_preferences).toHaveLength(1);
    expect(payment_preferences).toContainEqual(
      expect.objectContaining({
        payment_method: "Check",
        cheque_details: expect.objectContaining({
          name_to_print_on_check: `${claim.claim.first_name} ${claim.claim.last_name}`,
        }),
      })
    );
  });

  it("Should generate a valid SSN", async () => {
    const claim = await scenario("TEST", medical)(opts);
    new ParseSSN((claim.claim.tax_identifier ?? "").replace(/-/g, ""));
  });

  it("Should pull an employer from the pool", async () => {
    const employerFeins = employerPool.map((e) => e.fein);
    const claim = await scenario("TEST", medical)(opts);
    expect(employerFeins).toContain(claim.claim.employer_fein);
  });

  it("Should populate the mass_id property for mass proofed claims", async () => {
    const claim = await scenario("TEST", medical)(opts);
    expect(claim.claim.mass_id).toMatch(/^S(\d{8}|A\d{7})$/);
    expect(claim.claim.has_state_id).toBe(true);
  });

  it("Should populate the mass_id property for mass unproofed claims", async () => {
    const claim = await scenario("TEST", {
      ...medical,
      residence: "MA-unproofed",
    })(opts);
    expect(claim.claim.mass_id).toMatch(/^S(\d{8}|A\d{7})$/);
    expect(claim.claim.has_state_id).toBe(true);
  });

  it("Should not populate the mass_id property for OOS claims", async () => {
    const claim = await scenario("TEST", { ...medical, residence: "OOS" })(
      opts
    );
    expect(claim.claim.mass_id).toBe(null);
    expect(claim.claim.has_state_id).toBe(false);
  });

  it("Should default to generating financially eligible claims", async () => {
    const claim = await scenario("TEST", { ...medical, residence: "OOS" })(
      opts
    );
    expect(claim.financiallyIneligible).toBe(false);
  });

  it("Should populate financial eligibility field.", async () => {
    const claim = await scenario("TEST", {
      ...medical,
      financiallyIneligible: true,
    })(opts);
    expect(claim.financiallyIneligible).toBe(true);
  });

  it("Should have has_ properties that match its leave periods", async () => {
    const claim = await scenario("TEST", {
      ...medical,
      financiallyIneligible: true,
    })(opts);
    expect(claim.claim).toMatchObject({
      has_continuous_leave_periods: true,
      has_intermittent_leave_periods: false,
      has_reduced_schedule_leave_periods: false,
    });
  });

  it("Should generate an HCP form", async () => {
    const claim = await scenario("TEST", {
      ...medical,
      residence: "OOS",
    })(opts);

    expect(generators.HCP).toHaveBeenCalledWith(claim.claim, {});
  });

  it("Should generate requested documents", async () => {
    const claim = await scenario("TEST", {
      ...medical,
      docs: {
        HCP: { invalid: true },
        MASSID: {},
      },
    })(opts);

    expect(generators.HCP).toHaveBeenCalledWith(claim.claim, { invalid: true });
    expect(generators.MASSID).toHaveBeenCalledWith(claim.claim, {});
    await expect(
      fs.promises.stat(`${opts.documentDirectory}/${claim.documents[0].path}`)
    ).resolves.toBeTruthy();
    await expect(
      fs.promises.stat(`${opts.documentDirectory}/${claim.documents[1].path}`)
    ).resolves.toBeTruthy();
  });

  it("Should allow the generation of mailed documents", async () => {
    const claim = await scenario("TEST", {
      ...medical,
      docs: {
        HCP: { mailed: true },
        MASSID: {},
      },
    })(opts);

    expect(generators.HCP).toHaveBeenCalledWith(claim.claim, {});
    expect(claim.documents[0]).toMatchObject({
      submittedManually: true,
    });
    expect(claim.documents[1]).toMatchObject({
      submittedManually: false,
    });
  });

  function extractLeavePeriod(claim: SimulationClaim["claim"]): [Date, Date] {
    const period = claim.leave_details?.continuous_leave_periods?.[0];
    if (!period || !period.start_date || !period.end_date) {
      throw new Error("No leave period given");
    }
    return [new Date(period.start_date), new Date(period.end_date)];
  }

  function extractNotificationDate(claim: SimulationClaim["claim"]): Date {
    const str = claim.leave_details?.employer_notification_date;
    if (!str) {
      throw new Error("No notification date given");
    }
    return new Date(str);
  }

  it("Should have an application start date past 01/01/2021", async () => {
    const { claim } = await scenario("TEST", medical)(opts);
    const [start] = extractLeavePeriod(claim);
    expect(start.getTime()).toBeGreaterThan(new Date(2021, 0).getTime());
  });

  it("Should have an application end date greater/later than start date", async () => {
    const { claim } = await scenario("TEST", medical)(opts);
    const [start, end] = extractLeavePeriod(claim);
    expect(start.getTime()).toBeLessThan(end.getTime());
  });

  it("Should have an application end date within 20 weeks of the start date", async () => {
    const { claim } = await scenario("TEST", medical)(opts);
    const [start, end] = extractLeavePeriod(claim);
    expect(end.getTime() - start.getTime()).toBeLessThan(
      // 20 weeks worth of milliseconds...
      86400 * 1000 * 7 * 20
    );
  });

  it("Should have a notification date prior to the leave start date", async () => {
    const { claim } = await scenario("TEST", medical)(opts);
    const [start] = extractLeavePeriod(claim);
    const notification = extractNotificationDate(claim);

    expect(notification.getTime()).toBeLessThan(start.getTime());
  });

  it("Should have a notification date that qualifies as short notice", async () => {
    const { claim } = await scenario("TEST", medical)(opts);
    const [start] = extractLeavePeriod(claim);
    const notification = extractNotificationDate(claim);
    expect(notification.getTime()).toBeLessThanOrEqual(
      start.getTime() - 86400 * 1000
    );
  });

  it("Should generate a birth date 18-65 years in the past.", async () => {
    const { claim } = await scenario("TEST", medical)(opts);
    const { date_of_birth } = claim;
    if (typeof date_of_birth !== "string") {
      throw new Error("Expected date_of_birth to be a string");
    }
    const date = new Date(date_of_birth);

    expect(date.getFullYear()).toBeLessThanOrEqual(
      new Date().getFullYear() - 18
    );
    expect(date.getFullYear()).toBeGreaterThanOrEqual(
      new Date().getFullYear() - 65
    );
  });

  it("Should set the leave reason for medical claims", async () => {
    const { claim } = await scenario("TEST", medical)(opts);
    expect(claim.leave_details).toMatchObject({
      reason: medical.reason,
      reason_qualifier: medical.reason_qualifier,
    });
  });

  it("Should set the leave reason for bonding claims", async () => {
    const { claim } = await scenario("TEST", bonding)(opts);
    expect(claim.leave_details).toMatchObject({
      reason: bonding.reason,
      reason_qualifier: bonding.reason_qualifier,
    });
  });

  it("Should set the child birth date for bonding newborn claims", async () => {
    const { claim } = await scenario("TEST", bonding)(opts);
    expect(claim.leave_details?.child_birth_date).toMatch(/\d{4}-\d{2}-\d{2}/);
  });
  it("Should set the child placement date for bonding adoption claims", async () => {
    const { claim } = await scenario("TEST", {
      ...bonding,
      reason_qualifier: "Adoption",
    })(opts);
    expect(claim.leave_details?.child_placement_date).toMatch(
      /\d{4}-\d{2}-\d{2}/
    );
  });
  it("Should set the child placement date for bonding foster claims", async () => {
    const { claim } = await scenario("TEST", {
      ...bonding,
      reason_qualifier: "Foster Care",
    })(opts);
    expect(claim.leave_details?.child_placement_date).toMatch(
      /\d{4}-\d{2}-\d{2}/
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
