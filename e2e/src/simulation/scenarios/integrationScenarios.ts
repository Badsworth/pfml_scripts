import { scenario } from "../simulate";

// Additional scenarios for integration testing that should not be included in LST or BizSim
export const BHAP8 = scenario("BHAP8", {
  reason: "Child Bonding",
  reason_qualifier: "Foster Care",
  residence: "MA-proofed",
  docs: {
    HCP: {},
    MASSID: {},
  },
  has_reduced_schedule_leave_periods: true,
});

export const BHAP9 = scenario("BHAP9", {
  reason: "Child Bonding",
  reason_qualifier: "Foster Care",
  residence: "MA-proofed",
  docs: {
    HCP: {},
    MASSID: {},
  },
  has_intermittent_leave_periods: true,
});

// Mailed HCP, MA Resident, Bonding
export const BGBM1 = scenario("MGBM1", {
  reason: "Child Bonding",
  reason_qualifier: "Foster Care",
  residence: "MA-proofed",
  docs: {
    HCP: { mailed: true },
    MASSID: {},
  },
});
