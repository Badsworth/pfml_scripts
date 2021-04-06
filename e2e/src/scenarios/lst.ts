import { ScenarioSpecification } from "../generation/Scenario";
import * as CypressScenarios from "./cypress";

/**
 * Load & Stress Testing Scenarios.
 *
 */

// Portal claim submission with eligible employee
export const LSTBHAP1: ScenarioSpecification = {
  ...CypressScenarios.BHAP1,
  claim: {
    ...CypressScenarios.BHAP1.claim,
    label: "PortalClaimSubmit",
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
    },
  },
};

// Portal claim submission with ineligible employee
export const LSTBHAP4: ScenarioSpecification = {
  ...CypressScenarios.BHAP1INEL,
  claim: {
    ...CypressScenarios.BHAP1INEL.claim,
    label: "PortalClaimSubmit",
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Deny",
    },
  },
};

// Fineos claim submission with eligible employee
export const LSTFBHAP1: ScenarioSpecification = {
  ...CypressScenarios.BHAP1,
  claim: {
    ...CypressScenarios.BHAP1.claim,
    label: "FineosClaimSubmit",
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
    },
  },
};

// Fineos claim submission with ineligible employee
export const LSTFBHAP4: ScenarioSpecification = {
  ...CypressScenarios.BHAP1INEL,
  claim: {
    ...CypressScenarios.BHAP1INEL.claim,
    label: "FineosClaimSubmit",
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Deny",
    },
  },
};
