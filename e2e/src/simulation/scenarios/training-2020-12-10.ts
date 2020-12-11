import { scenario, chance } from "../simulate";

export const MCS = scenario("MCS", {
  reason: "Serious Health Condition - Employee",
  residence: "MA-proofed",
  has_continuous_leave_periods: true,
  docs: {
    MASSID: {},
    HCP: {},
  },
});
const MC = MCS;

export const MIS = scenario("MIS", {
  reason: "Serious Health Condition - Employee",
  residence: "MA-proofed",
  has_intermittent_leave_periods: true,
  docs: {
    MASSID: {},
    HCP: {},
  },
});
const MI = MIS;

export const MRS = scenario("MRS", {
  reason: "Serious Health Condition - Employee",
  residence: "MA-proofed",
  has_intermittent_leave_periods: true,
  docs: {
    MASSID: {},
    HCP: {},
  },
});
const MR = MRS;

export const INVALIDMED = scenario("INVALIDMED", {
  reason: "Serious Health Condition - Employee",
  has_reduced_schedule_leave_periods: true,
  residence: "MA-proofed",
  docs: {
    MASSID: { invalid: true },
    HCP: { invalid: true },
  },
});

export const PREBIRTHMED = scenario("PREBIRTH", {
  reason: "Serious Health Condition - Employee",
  has_reduced_schedule_leave_periods: true,
  residence: "MA-proofed",
  pregnant_or_recent_birth: true,
  docs: {
    MASSID: { invalid: true },
    HCP: { invalid: true },
  },
});

export default chance([
  [235, MC],
  [235, MI],
  [235, MR],
  [50, INVALIDMED],
  [225, PREBIRTHMED],
]);
