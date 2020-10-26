import { scenario } from "../simulate";

// Additional scenarios for integration testing that should not be included in LST or BizSim
export const MHAP4 = scenario("HAP4", {
  reason: "Serious Health Condition - Employee",
  residence: "MA-proofed",
  docs: {
    HCP: {},
    MASSID: {},
  },
  has_reduced_schedule_leave_periods: true,
});

export const MHAP5 = scenario("MHAP5", {
  reason: "Serious Health Condition - Employee",
  residence: "MA-proofed",
  docs: {
    HCP: {},
    MASSID: {},
  },
  has_intermittent_leave_periods: true,
});
