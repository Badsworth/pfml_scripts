import { ScenarioSpecification } from "../generation/Scenario";
import * as CypressScenarios from "./cypress";
import { getCaringLeaveStartEndDates } from "../util/claims";

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

export const LSTCHAP1: ScenarioSpecification = {
  employee: {
    wages: "eligible",
    mass_id: true,
  },
  claim: {
    label: "CCAP90",
    reason: "Care for a Family Member",
    work_pattern_spec: "0,720,0,720,0,720,0",
    docs: { MASSID: {}, CARING: {} },
    leave_dates: getCaringLeaveStartEndDates(),
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
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
