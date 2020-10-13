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
const HAP1 = scenario("HAP1", {
  reason: "Serious Health Condition - Employee",
  reason_qualifier: "Serious Health Condition",
  residence: "MA-proofed",
  docs: {
    HCP: {},
    MASSID: {},
  },
});
// Simple claim, OOS resident.
const HAP2 = scenario("HAP2", {
  reason: "Serious Health Condition - Employee",
  reason_qualifier: "Serious Health Condition",
  residence: "OOS",
  docs: {
    HCP: {},
    OOSID: {},
  },
});
// Simple denial, MA resident.
const HAP3 = scenario("HAP3", {
  reason: "Serious Health Condition - Employee",
  reason_qualifier: "Serious Health Condition",
  residence: "MA-proofed",
  financiallyIneligible: true,
  docs: {
    HCP: {},
    MASSID: {},
  },
});

// Combine Happy path scenarios into a single group:
const HAP = chance([
  [1, HAP1],
  [1, HAP2],
  [1, HAP3],
]);

/*****
  Good But ... Scenarios
******/

// Missing HCP, MA Resident
const GBR1 = scenario("GBR1", {
  reason: "Serious Health Condition - Employee",
  reason_qualifier: "Serious Health Condition",
  residence: "MA-proofed",
  docs: {
    MASSID: {},
  },
});

// Mailed HCP, MA Resident
const GBM1 = scenario("GBM1", {
  reason: "Serious Health Condition - Employee",
  reason_qualifier: "Serious Health Condition",
  residence: "MA-proofed",
  docs: {
    HCP: { mailed: true },
    MASSID: {},
  },
});

// Missing HCP, Out of State Resident
const GBR2 = scenario("GBR2", {
  reason: "Serious Health Condition - Employee",
  reason_qualifier: "Serious Health Condition",
  residence: "OOS",
  docs: {
    OOSID: {},
  },
});

// Mailed HCP, Out of State Resident
const GBM2 = scenario("GBM2", {
  reason: "Serious Health Condition - Employee",
  reason_qualifier: "Serious Health Condition",
  residence: "OOS",
  docs: {
    HCP: { mailed: true },
    OOSID: {},
  },
});

//Combine Good but ... path scenarios into a single group:
const GB = chance([
  [1, GBR1],
  [1, GBM1],
  [1, GBR2],
  [1, GBM2],
]);

// HCP sent before an application is started
const UNH1 = scenario("UNH1", {
  reason: "Serious Health Condition - Employee",
  reason_qualifier: "Serious Health Condition",
  residence: "MA-proofed",
  docs: {
    HCP: { mailed: true },
  },
  skipSubmitClaim: true,
});
// Invalid HCP
const UNH2 = scenario("UNH2", {
  reason: "Serious Health Condition - Employee",
  reason_qualifier: "Serious Health Condition",
  residence: "OOS",
  docs: {
    HCP: { invalid: true },
    OOSID: {},
  },
});
// Mismatched ID/SSN
const UNH3 = scenario("UNH3", {
  reason: "Serious Health Condition - Employee",
  reason_qualifier: "Serious Health Condition",
  residence: "MA-unproofed",
  docs: {
    OOSID: { invalid: true },
  },
});
// Short Notice
const UNH4 = scenario("UNH4", {
  reason: "Serious Health Condition - Employee",
  reason_qualifier: "Serious Health Condition",
  residence: "MA-proofed",
  shortNotice: true,
  docs: {
    HCP: {},
    OOSID: {},
  },
});
const UNH = chance([
  [1, UNH1],
  [1, UNH2],
  [1, UNH3],
  [1, UNH4],
]);

// Chance Function for all combinations!
export default chance([
  [1, HAP],
  [1, GB],
  [1, UNH],
]);
