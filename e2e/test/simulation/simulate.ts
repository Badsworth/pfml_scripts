import { describe, it, expect, jest } from "@jest/globals";
import {
  scenario,
  chance,
  ScenarioOpts,
  generateLeaveDates,
} from "../../src/simulation/simulate";
import type { SimulationClaim } from "../../src/simulation/types";
import generators from "../../src/simulation/documents";
import fs from "fs";
import { extractLeavePeriod } from "../../src/utils";
import { fromEmployersFactory } from "../../src/simulation/EmployerFactory";
import employerPool from "../../src/simulation/fixtures/employerPool";
import { WorkPattern } from "../../src/api";
import { format } from "date-fns";

jest.mock("../../src/simulation/documents");

const opts = {
  documentDirectory: "/tmp",
  employeeFactory: jest.fn(() => {
    return {
      first_name: "John",
      last_name: "Doe",
      employer_fein: "00-000000",
      tax_identifier: "000-00-0000",
    };
  }),
  employerFactory: jest.fn(fromEmployersFactory(employerPool)),
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

const reduced: ScenarioOpts = {
  residence: "MA-proofed",
  reason: "Child Bonding",
  reason_qualifier: "Newborn",
  bondingDate: "past",
  docs: {
    HCP: {},
    MASSID: {},
  },
  has_reduced_schedule_leave_periods: true,
};

const intermittent: ScenarioOpts = {
  residence: "MA-proofed",
  reason: "Child Bonding",
  reason_qualifier: "Newborn",
  bondingDate: "past",
  docs: {
    HCP: {},
    MASSID: {},
  },
  has_intermittent_leave_periods: true,
};

describe("Simulation Generator", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("Should generate a unique ID for each simulation claim", async () => {
    const claim1 = await scenario("TEST", medical)(opts);
    const claim2 = await scenario("TEST", medical)(opts);
    expect(claim1).toHaveProperty("id", expect.any(String));
    expect(claim2).toHaveProperty("id", expect.any(String));
    expect(claim1.id).not.toEqual(claim2.id);
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

  // Test removed until payment feature becomes available
  // it("Should have payment information", async () => {
  //   const claim = await scenario("TEST", medical)(opts);
  //   const { payment_preferences } = claim.claim;
  //   expect(payment_preferences).toHaveLength(1);
  //   expect(payment_preferences).toContainEqual(
  //     expect.objectContaining({
  //       payment_method: "Check",
  //       cheque_details: expect.objectContaining({
  //         name_to_print_on_check: `${claim.claim.first_name} ${claim.claim.last_name}`,
  //       }),
  //     })
  //   );
  // });

  it("Should pass arguments to the employee factory", async () => {
    await scenario("TEST", { ...medical })(opts);
    expect(opts.employeeFactory).toHaveBeenCalledWith(
      false,
      opts.employerFactory
    );
    await scenario("TEST", { ...medical, financiallyIneligible: true })(opts);
    expect(opts.employeeFactory).toHaveBeenCalledWith(
      true,
      opts.employerFactory
    );
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
    await expect(scenario("TEST", medical)(opts)).resolves.toMatchObject({
      claim: {
        has_continuous_leave_periods: true,
        has_intermittent_leave_periods: false,
        has_reduced_schedule_leave_periods: false,
      },
    });
    await expect(scenario("TEST", intermittent)(opts)).resolves.toMatchObject({
      claim: {
        has_continuous_leave_periods: false,
        has_intermittent_leave_periods: true,
        has_reduced_schedule_leave_periods: false,
      },
    });
    await expect(scenario("TEST", reduced)(opts)).resolves.toMatchObject({
      claim: {
        has_continuous_leave_periods: false,
        has_intermittent_leave_periods: false,
        has_reduced_schedule_leave_periods: true,
      },
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

  function extractNotificationDate(claim: SimulationClaim["claim"]): Date {
    const str = claim.leave_details?.employer_notification_date;
    if (!str) {
      throw new Error("No notification date given");
    }
    return new Date(str);
  }

  it("Should have an application start date past 01/01/2021", async () => {
    // We run through this test 100 times, because we're dealing with randomness
    // and need to be sure we're always getting a valid result.
    for (let i = 0; i < 100; i++) {
      const claim = await scenario("TEST", medical)(opts);
      const period = claim.claim.leave_details?.continuous_leave_periods?.[0];
      if (period === null || period === undefined) {
        throw new Error("No period was present on the claim");
      }
      expect(period?.start_date).toMatch(/^2021\-/);
    }
  });

  it("Should have an application end date greater/later than start date", async () => {
    const { claim } = await scenario("TEST", medical)(opts);
    const [start, end] = extractLeavePeriod(claim);
    expect(start.getTime()).toBeLessThan(end.getTime());
  });

  it("Should allow for a short leave period to be generated", async () => {
    const { claim } = await scenario("TEST", { ...medical, shortClaim: true })(
      opts
    );
    const [start, end] = extractLeavePeriod(claim);
    // End - start should = 7 days worth of seconds.
    expect(end.getTime() - start.getTime()).toEqual(24 * 60 * 60 * 1000);
  });

  it("Should allow for arbitrary scenario configuration to be overridden by options", async () => {
    const { claim } = await scenario(
      "TEST",
      medical
    )({ ...opts, shortClaim: true });
    const [start, end] = extractLeavePeriod(claim);
    // End - start should = 7 days worth of seconds.
    expect(end.getTime() - start.getTime()).toEqual(24 * 60 * 60 * 1000);
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

  it("Should create a reduced leave claim", async () => {
    const { claim } = await scenario("TEST", reduced)(opts);
    const [start, end] = extractLeavePeriod(
      claim,
      "reduced_schedule_leave_periods"
    );
    expect(start.getTime()).toBeLessThan(end.getTime());
    expect(claim.leave_details?.reduced_schedule_leave_periods).toEqual([
      expect.objectContaining({
        sunday_off_minutes: 0,
        monday_off_minutes: 240,
        tuesday_off_minutes: 240,
        wednesday_off_minutes: 240,
        thursday_off_minutes: 240,
        friday_off_minutes: 240,
        saturday_off_minutes: 0,
      }),
    ]);
  });

  it("Should create a reduced leave claim for a rotating shift pattern", async () => {
    const { claim } = await scenario("TEST", {
      ...reduced,
      work_pattern_type: "rotating_shift",
    })(opts);
    const [start, end] = extractLeavePeriod(
      claim,
      "reduced_schedule_leave_periods"
    );
    expect(start.getTime()).toBeLessThan(end.getTime());
    expect(claim.leave_details?.reduced_schedule_leave_periods).toEqual([
      expect.objectContaining({
        sunday_off_minutes: 0,
        monday_off_minutes: 360,
        tuesday_off_minutes: 0,
        wednesday_off_minutes: 360,
        thursday_off_minutes: 0,
        friday_off_minutes: 360,
        saturday_off_minutes: 0,
      }),
    ]);
  });

  it("Should create a claim with a rotating schedule", async () => {
    const { claim } = await scenario("TEST", {
      ...medical,
      work_pattern_type: "rotating_shift",
    })(opts);
    expect(claim.work_pattern).toEqual({
      work_pattern_type: "Rotating",
      work_week_starts: "Monday",
      work_pattern_days: [
        { day_of_week: "Sunday", minutes: 0, week_number: 1 },
        { day_of_week: "Monday", minutes: 720, week_number: 1 },
        { day_of_week: "Tuesday", minutes: 0, week_number: 1 },
        { day_of_week: "Wednesday", minutes: 720, week_number: 1 },
        { day_of_week: "Thursday", minutes: 0, week_number: 1 },
        { day_of_week: "Friday", minutes: 720, week_number: 1 },
        { day_of_week: "Saturday", minutes: 0, week_number: 1 },
        { day_of_week: "Sunday", minutes: 720, week_number: 2 },
        { day_of_week: "Monday", minutes: 0, week_number: 2 },
        { day_of_week: "Tuesday", minutes: 720, week_number: 2 },
        { day_of_week: "Wednesday", minutes: 0, week_number: 2 },
        { day_of_week: "Thursday", minutes: 720, week_number: 2 },
        { day_of_week: "Friday", minutes: 0, week_number: 2 },
        { day_of_week: "Saturday", minutes: 0, week_number: 2 },
      ],
    });
  });

  it("Should create an intermittent leave claim", async () => {
    const { claim } = await scenario("TEST", intermittent)(opts);
    const [start, end] = extractLeavePeriod(
      claim,
      "intermittent_leave_periods"
    );
    expect(start.getTime()).toBeLessThan(end.getTime());
  });

  it("Should not set pregnant_or_given_birth unless requested to do so", async () => {
    const { claim } = await scenario("TEST", medical)(opts);
    expect(claim).toMatchObject({
      leave_details: expect.objectContaining({
        pregnant_or_recent_birth: false,
      }),
    });
  });

  it("Should allow for medical pre-birth claims to be created", async () => {
    const { claim } = await scenario("TEST", {
      ...medical,
      pregnant_or_recent_birth: true,
    })(opts);
    expect(claim).toMatchObject({
      leave_details: expect.objectContaining({
        pregnant_or_recent_birth: true,
      }),
    });
  });
});

describe("Leave date generator", () => {
  it("Should always generate a correct date for a given work schedule.", () => {
    const schedule: WorkPattern = {
      work_pattern_days: [{ day_of_week: "Monday", minutes: 10 }],
    };
    for (let i = 0; i < 1000; i++) {
      const [start] = generateLeaveDates(schedule);
      expect(format(start, "iiii")).toEqual("Monday");
    }
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
