import { chance, scenario, agentScenario } from "../simulate";

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
 * "PortalClaimSubmit" scenario
 * "FineosClaimSubmit" scenario
 * "SavilinxAgent" scenario
 *   * "Adjudicate Absence"
 *     * between approval or denial
 *   * "Document Review"
 *     * can trigger "Request Additional Information" when document is missing
 */

/*
  LeaveAdminSelfRegistration
*/
export const LeaveAdminSelfReg = agentScenario("LeaveAdminSelfRegistration");

/*
  SavilinxAgent
*/
export const SavilinxAgent = agentScenario("SavilinxAgent");

/* Will be used on LST Soft/Full Launch */
// Happy Path Foster
export const BHAP1 = scenario("PortalClaimSubmit", {
  reason: "Child Bonding",
  reason_qualifier: "Foster Care",
  residence: "MA-proofed",
  docs: {
    MASSID: {},
    FOSTERPLACEMENT: {},
  },
});

// Happy path denial due to financial eligibility.
export const BHAP4 = scenario("PortalClaimSubmit", {
  reason: "Child Bonding",
  reason_qualifier: "Newborn",
  residence: "OOS",
  wages: "ineligible",
  bondingDate: "past",
  docs: {
    OOSID: {},
    BIRTHCERTIFICATE: {},
  },
});

// Missing Foster Documentation
export const BGBM1 = scenario("PortalClaimSubmit", {
  reason: "Child Bonding",
  reason_qualifier: "Foster Care",
  residence: "MA-proofed",
  docs: {
    MASSID: {},
  },
});

export const FBHAP1 = scenario("FineosClaimSubmit", {
  reason: "Child Bonding",
  reason_qualifier: "Foster Care",
  residence: "MA-proofed",
  docs: {
    MASSID: {},
    FOSTERPLACEMENT: {},
  },
});

export const FBHAP4 = scenario("FineosClaimSubmit", {
  reason: "Child Bonding",
  reason_qualifier: "Newborn",
  residence: "OOS",
  wages: "ineligible",
  bondingDate: "past",
  docs: {
    OOSID: {},
    BIRTHCERTIFICATE: {},
  },
});

export const FBGBM1 = scenario("FineosClaimSubmit", {
  reason: "Child Bonding",
  reason_qualifier: "Foster Care",
  residence: "MA-proofed",
  docs: {
    MASSID: {},
  },
});

// BHAP1 ? PortalClaimSubmit : FineosClaimSubmit
export const combinedBHAP1 = chance([
  [1, BHAP1],
  [1, FBHAP1],
]);

// BHAP4 ? PortalClaimSubmit : FineosClaimSubmit
export const combinedBHAP4 = chance([
  [1, BHAP4],
  [1, FBHAP4],
]);

// BGBM1 ? PortalClaimSubmit : FineosClaimSubmit
export const combinedBGBM1 = chance([
  [1, BGBM1],
  [1, FBGBM1],
]);

// Flood 1st Stream's Dataset
// 11 concurrent claim submissions
export default chance([
  [17, combinedBHAP1], // 85%, eligible
  [2, combinedBHAP4], // 10%, not
  [1, combinedBGBM1], // 5%, eligible but missing doc
]);

// Flood 2nd Stream's Dataset
// 180 concurrent Savilinx Agents
// make it a default export generate this dataset
// export default chance([[1, SavilinxAgent]]);

// Flood Leave Admin run
// export default chance([[1, LeaveAdminSelfReg]]);
