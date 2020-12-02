import { scenario, /* agentScenario, */ chance } from "../simulate";

/**
 * This file contains the business simulation for Pilot 3.
 *
 * The overall simulation consists of several groups. Within each group, a number
 * of scenarios are defined. Each time this scenario's generator is invoked, it
 * returns a single scenario, selected by probability.
 *
 * @see chance()
 * @see generate()
 *
 * Happy Path Scenarios
 * HAP1 -> Simple claim, MA resident
 * HAP3 -> Simple denial, MA resident
 *
 * Good But... Path Scenarios
 * GBR1 -> Missing HCP, MA Resident
 * GBR2 -> Missing ID, MA Resident
 *
 * "PortalRegistration" scenario
 * "PortalClaimSubmit" scenario
 * "FineosClaimSubmit" scenario
 * "SavilinxAgent" scenario
 *   * "Adjudicate Absence"
 *     * between approval or denial
 *   * "Outstanding Document Received"
 *     * can trigger "Request Additional Information" when document is missing
 */

/*
  PortalRegistration
*/
// const PortalRegistration = agentScenario("PortalRegistration");

/*
  LeaveAdminSelfRegistration

const LeaveAdminSelfReg = agentScenario("LeaveAdminSelfRegistration", {
  claim: {
    employer_fein: "yes",
  },
});
*/
/* 
  SavilinxAgent
*/
// const SavilinxAgent = agentScenario("SavilinxAgent");

/* Will be used on LST Soft/Full Launch */
// Happy Path Foster
const BHAP1 = scenario("PortalClaimSubmit", {
  reason: "Child Bonding",
  reason_qualifier: "Foster Care",
  residence: "MA-proofed",
  docs: {
    MASSID: {},
    FOSTERPLACEMENT: {},
  },
});

// Happy path denial due to financial eligibility.
const BHAP4 = scenario("PortalClaimSubmit", {
  reason: "Child Bonding",
  reason_qualifier: "Newborn",
  residence: "OOS",
  financiallyIneligible: true,
  bondingDate: "past",
  docs: {
    OOSID: {},
    BIRTHCERTIFICATE: {},
  },
});

// Missing Foster Documentation
const BGBM1 = scenario("PortalClaimSubmit", {
  reason: "Child Bonding",
  reason_qualifier: "Foster Care",
  residence: "MA-proofed",
  docs: {
    MASSID: {},
  },
});

const FBHAP1 = scenario("FineosClaimSubmit", {
  reason: "Child Bonding",
  reason_qualifier: "Foster Care",
  residence: "MA-proofed",
  docs: {
    MASSID: {},
    FOSTERPLACEMENT: {},
  },
});

const FBHAP4 = scenario("FineosClaimSubmit", {
  reason: "Child Bonding",
  reason_qualifier: "Newborn",
  residence: "OOS",
  financiallyIneligible: true,
  bondingDate: "past",
  docs: {
    OOSID: {},
    BIRTHCERTIFICATE: {},
  },
});

const FBGBM1 = scenario("FineosClaimSubmit", {
  reason: "Child Bonding",
  reason_qualifier: "Foster Care",
  residence: "MA-proofed",
  docs: {
    MASSID: {},
  },
});

// BHAP1 ? PortalClaimSubmit : FineosClaimSubmit
const _BHAP1 = chance([
  [1, BHAP1],
  [1, FBHAP1],
]);

// BHAP4 ? PortalClaimSubmit : FineosClaimSubmit
const _BHAP4 = chance([
  [1, BHAP4],
  [1, FBHAP4],
]);

// BGBM1 ? PortalClaimSubmit : FineosClaimSubmit
const _BGBM1 = chance([
  [1, BGBM1],
  [1, FBGBM1],
]);

// Flood 1st Stream's Dataset
// 11 concurrent claim submissions
export default chance([
  [17, _BHAP1], // 85%, eligible
  [2, _BHAP4], // 10%, not
  [1, _BGBM1], // 5%, eligible but missing doc
]);

// Flood 2nd Stream's Dataset
// 180 concurrent Savilinx Agents
// make it a default export generate this dataset
// export default chance([[1, SavilinxAgent]]);

// Flood Leave Admin run
// export default chance([[1, LeaveAdminSelfReg]]);
