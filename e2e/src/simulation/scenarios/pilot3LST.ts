import { scenario, agentScenario, chance } from "../simulate";

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
  HAP1 -> Simple claim, MA resident
  HAP3 -> Simple denial, MA resident

  Good But... Path Scenarios
  GBR1 -> Missing HCP, MA Resident
  GBR2 -> Missing ID, MA Resident

  "PortalClaimSubmit" scenario
  "FineosClaimSubmit" scenario
  "SavilinxAgent" scenario
    * "Adjudicate Absence"
      * between approval or denial
    * "Outstanding Document Received"
      * can trigger "Request Additional Information" when document is missing
******/

/*
  PortalRegistration
*/
const PortalRegistration = agentScenario("PortalRegistration");

/*
  PortalClaimSubmit
*/
const HAP1Portal = scenario("PortalClaimSubmit", {
  reason: "Serious Health Condition - Employee",
  reason_qualifier: "Serious Health Condition",
  residence: "MA-proofed",
  docs: {
    MASSID: {},
    HCP: {},
  },
});

const GBR1Portal = scenario("PortalClaimSubmit", {
  reason: "Serious Health Condition - Employee",
  reason_qualifier: "Serious Health Condition",
  residence: "MA-proofed",
  docs: {
    MASSID: {},
  },
});

const HAP3Portal = scenario("PortalClaimSubmit", {
  reason: "Serious Health Condition - Employee",
  reason_qualifier: "Serious Health Condition",
  residence: "MA-proofed",
  docs: {
    MASSID: {},
    HCP: {},
  },
  financiallyIneligible: true,
});

const HAPPortal = chance([
  [2, HAP1Portal],
  [1, GBR1Portal],
  [1, HAP3Portal],
]);

/*
  FineosClaimSubmit
*/
const HAP1Fineos = scenario("FineosClaimSubmit", {
  reason: "Serious Health Condition - Employee",
  reason_qualifier: "Serious Health Condition",
  residence: "MA-proofed",
  docs: {
    MASSID: {},
    HCP: {},
  },
});

const GBR1Fineos = scenario("PortalClaimSubmit", {
  reason: "Serious Health Condition - Employee",
  reason_qualifier: "Serious Health Condition",
  residence: "MA-proofed",
  docs: {
    MASSID: {},
  },
});

const HAP3Fineos = scenario("FineosClaimSubmit", {
  reason: "Serious Health Condition - Employee",
  reason_qualifier: "Serious Health Condition",
  residence: "MA-proofed",
  docs: {
    MASSID: {},
    HCP: {},
  },
  financiallyIneligible: true,
});

const HAPFineos = chance([
  [2, HAP1Fineos],
  [1, GBR1Fineos],
  [1, HAP3Fineos],
]);

/*
  SavilinxAgent - do only "Adjudicate Absence" tasks
*/
const SavilinxAgent = agentScenario("SavilinxAgent", {
  priorityTask: "Adjudicate Absence",
});

// Chance Function for all combinations!
export default chance([
  [3, HAPPortal],
  [2, HAPFineos],
  [7, SavilinxAgent],
  [2, PortalRegistration],
]);
