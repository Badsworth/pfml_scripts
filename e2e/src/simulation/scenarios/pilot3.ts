import { scenario, chance } from "../simulate";

/**
 * This file contains the business simulation for Pilot 3.
 *
 * The overall simulation consists of several groups. Within each group, a number
 * of scenarios are defined. Each time this scenario's generator is invoked, it
 * returns a single scenario, selected by probability.
 *
 * @see chance()
 * @see generate()
 */

/*****
  Happy Path Scenarios
******/

//Simple claim, MA resident:
export const MHAP1 = scenario("MHAP1", {
  reason: "Serious Health Condition - Employee",
  residence: "MA-proofed",
  docs: {
    HCP: {},
    MASSID: {},
  },
});
// Simple claim, OOS resident.
export const MHAP2 = scenario("MHAP2", {
  reason: "Serious Health Condition - Employee",
  residence: "OOS",
  docs: {
    HCP: {},
    OOSID: {},
  },
});
// Simple denial, MA resident.
export const MHAP3 = scenario("MHAP3", {
  reason: "Serious Health Condition - Employee",
  residence: "MA-proofed",
  wages: "ineligible",
  docs: {
    HCP: {},
    MASSID: {},
  },
});

// Combine Happy path scenarios into a single group:
export const MHAP = chance([
  [1, MHAP1],
  [1, MHAP2],
  [1, MHAP3],
]);

/*****
  Good But ... Scenarios
******/

// Missing HCP, MA Resident
export const MGBR1 = scenario("MGBR1", {
  reason: "Serious Health Condition - Employee",
  residence: "MA-proofed",
  docs: {
    MASSID: {},
  },
});

// Mailed HCP, MA Resident
export const MGBM1 = scenario("MGBM1", {
  reason: "Serious Health Condition - Employee",
  residence: "MA-proofed",
  docs: {
    HCP: { mailed: true },
    MASSID: {},
  },
});

// Missing HCP, Out of State Resident
export const MGBR2 = scenario("MGBR2", {
  reason: "Serious Health Condition - Employee",
  residence: "OOS",
  docs: {
    OOSID: {},
  },
});

// Mailed HCP, Out of State Resident
export const MGBM2 = scenario("MGBM2", {
  reason: "Serious Health Condition - Employee",
  residence: "OOS",
  docs: {
    HCP: { mailed: true },
    OOSID: {},
  },
});

//Combine Good but ... path scenarios into a single group:
const MGB = chance([
  [1, MGBR1],
  [1, MGBM1],
  [1, MGBR2],
  [1, MGBM2],
]);

// HCP sent before an application is started
export const MUNH1 = scenario("MUNH1", {
  reason: "Serious Health Condition - Employee",
  residence: "MA-proofed",
  docs: {
    HCP: { mailed: true },
  },
  skipSubmitClaim: true,
});
// Invalid HCP
export const MUNH2 = scenario("MUNH2", {
  reason: "Serious Health Condition - Employee",
  residence: "OOS",
  docs: {
    HCP: { invalid: true },
    OOSID: {},
  },
});
// Mismatched ID/SSN
export const MUNH3 = scenario("MUNH3", {
  reason: "Serious Health Condition - Employee",
  residence: "MA-unproofed",
  docs: {
    OOSID: { invalid: true },
  },
});
// Short Notice
export const MUNH4 = scenario("MUNH4", {
  reason: "Serious Health Condition - Employee",
  residence: "MA-proofed",
  shortNotice: true,
  docs: {
    HCP: {},
    OOSID: {},
  },
});
const MUNH = chance([
  [1, MUNH1],
  [1, MUNH2],
  [1, MUNH3],
  [1, MUNH4],
]);

// Chance Function for all combinations!
export default chance([
  [1, MHAP],
  [1, MGB],
  [1, MUNH],
]);
