import { describe, it, expect, jest } from "@jest/globals";
import { scenario, chance, ScenarioOpts } from "../../src/simulation/simulate";
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
    const claim = await scenario("TEST", { residence: "MA-proofed" })(opts);
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
    const claim = await scenario("TEST", { residence: "MA-proofed" })(opts);
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

  it("Should pull an employer from the pool", async () => {
    const employerFeins = employerPool.map((e) => e.fein);
    const claim = await scenario("TEST", { residence: "MA-proofed" })(opts);
    expect(employerFeins).toContain(claim.claim.employer_fein);
  });

  it("Should populate the mass_id property for mass proofed claims", async () => {
    const claim = await scenario("TEST", { residence: "MA-proofed" })(opts);
    expect(claim.claim.mass_id).toBeTruthy();
    expect(claim.claim.has_state_id).toBe(true);
  });

  it("Should populate the mass_id property for mass unproofed claims", async () => {
    const claim = await scenario("TEST", { residence: "MA-unproofed" })(opts);
    expect(claim.claim.mass_id).toBeTruthy();
    expect(claim.claim.has_state_id).toBe(true);
  });

  it("Should not populate the mass_id property for OOS claims", async () => {
    const claim = await scenario("TEST", { residence: "OOS" })(opts);
    expect(claim.claim.mass_id).toBe(null);
    expect(claim.claim.has_state_id).toBe(false);
  });

  it("Should default to generating financially eligible claims", async () => {
    const claim = await scenario("TEST", { residence: "OOS" })(opts);
    expect(claim.financiallyIneligible).toBe(false);
  });

  it("Should populate financial eligibility field.", async () => {
    const claim = await scenario("TEST", {
      residence: "OOS",
      financiallyIneligible: true,
    })(opts);
    expect(claim.financiallyIneligible).toBe(true);
  });

  it("Should generate an HCP form", async () => {
    const claim = await scenario("TEST", {
      residence: "OOS",
    })(opts);

    expect(generateHCP).toHaveBeenCalledWith(
      claim.claim,
      expect.stringMatching(/^\/tmp\/[\d-]+\.hcp\.pdf/),
      false
    );
  });

  it("Should generate an invalid HCP form", async () => {
    const claim = await scenario("TEST", {
      residence: "OOS",
      invalidHCP: true,
    })(opts);

    expect(generateHCP).toHaveBeenCalledWith(
      claim.claim,
      expect.stringMatching(/^\/tmp\/[\d-]+\.hcp\.pdf/),
      true
    );
  });

  it("Should generate an License Front", async () => {
    const config = { residence: "OOS" } as ScenarioOpts;
    const claim = await scenario("TEST", config)(opts);

    expect(generateIDFront).toHaveBeenCalledWith(
      claim.claim,
      expect.stringMatching(/^\/tmp\/[\d-]+\.id-front\.pdf/),
      false
    );
  });

  it("Should generate a license back", async () => {
    const claim = await scenario("TEST", {
      residence: "OOS",
    })(opts);
    expect(generateIDBack).toHaveBeenCalledWith(
      claim.claim,
      expect.stringMatching(/^\/tmp\/[\d-]+\.id-back\.pdf/)
    );
  });

  it("Should not add HCP form to Documents", async () => {
    const claim = await scenario("TEST", {
      residence: "MA-proofed",
      missingDocs: ["HCP"],
    })(opts);
    claim.documents.forEach((doc) => {
      expect(doc.type).not.toEqual("HCP");
    });
  });

  it("HCP Form should be submitted Manually", async () => {
    const claim = await scenario("TEST", {
      residence: "MA-proofed",
      mailedDocs: ["HCP"],
    })(opts);
    expect(claim.documents).toContainEqual(
      expect.objectContaining({
        type: "HCP",
        submittedManually: true,
      })
    );
  });

  it("Should not submit a claim nor generate an ID when an HCP was mailed before applying", async () => {
    const claim = await scenario("TEST", {
      residence: "MA-proofed",
      mailedDocs: ["HCP"],
      missingDocs: ["ID"],
      skipSubmitClaim: true,
    })(opts);
    expect(claim.documents).toContainEqual(
      expect.objectContaining({
        type: "HCP",
        submittedManually: true,
      })
    );
    expect(claim.documents).not.toContainEqual(
      expect.objectContaining({
        type: "ID-front",
      })
    );
    expect(claim.documents).not.toContainEqual(
      expect.objectContaining({
        type: "ID-back",
      })
    );
    expect(claim.skipSubmitClaim).toBeTruthy();
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
    const { claim } = await scenario("TEST", {
      residence: "MA-proofed",
    })(opts);
    const [start] = extractLeavePeriod(claim);
    expect(start.getTime()).toBeGreaterThan(new Date(2021, 0).getTime());
  });

  it("Should have an application end date greater/later than start date", async () => {
    const { claim } = await scenario("TEST", {
      residence: "MA-proofed",
    })(opts);
    const [start, end] = extractLeavePeriod(claim);
    expect(start.getTime()).toBeLessThan(end.getTime());
  });

  it("Should have an application end date within 20 weeks of the start date", async () => {
    const { claim } = await scenario("TEST", {
      residence: "MA-proofed",
    })(opts);
    const [start, end] = extractLeavePeriod(claim);
    expect(end.getTime() - start.getTime()).toBeLessThan(
      // 20 weeks worth of milliseconds...
      86400 * 1000 * 7 * 20
    );
  });

  it("Should have a notification date prior to the leave start date", async () => {
    const { claim } = await scenario("TEST", {
      residence: "MA-proofed",
    })(opts);
    const [start] = extractLeavePeriod(claim);
    const notification = extractNotificationDate(claim);

    expect(notification.getTime()).toBeLessThan(start.getTime());
  });

  it("Should have a notification date that qualifies as short notice", async () => {
    const { claim } = await scenario("TEST", {
      residence: "MA-proofed",
      shortNotice: true,
    })(opts);
    const [start] = extractLeavePeriod(claim);
    const notification = extractNotificationDate(claim);
    expect(notification.getTime()).toBeLessThanOrEqual(
      start.getTime() - 86400 * 1000
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
