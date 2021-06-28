import { ScenarioSpecification } from "../generation/Scenario";
import * as CypressScenarios from "./cypress";
import { getCaringLeaveStartEndDates } from "../util/claims";
import { EmployerResponseSpec } from "../generation/Claim";

/**
 * Load & Stress Testing Scenarios.
 *
 */

const otherLeavesAndBenefitsProps: Partial<ScenarioSpecification["claim"]> = {
  other_incomes: [
    {
      income_type: "Earnings from another employment/self-employment",
      income_amount_dollars: 200,
      income_amount_frequency: "Per Week",
    },
  ],
  employer_benefits: [
    {
      benefit_amount_dollars: 100,
      benefit_amount_frequency: "Per Week",
      benefit_type: "Short-term disability insurance",
      is_full_salary_continuous: false,
    },
  ],
  previous_leaves_other_reason: [
    {
      type: "other_reason",
      leave_reason: "Bonding with my child after birth or placement",
      is_for_current_employer: true,
      leave_minutes: 2400,
      worked_per_week_minutes: 1200,
    },
  ],
  concurrent_leave: { is_for_current_employer: true },
};

const employerResponseLeavesAndBenefits: Partial<EmployerResponseSpec> = {
  employer_benefits: [
    {
      benefit_amount_dollars: 200,
      benefit_amount_frequency: "Per Week",
      benefit_type: "Short-term disability insurance",
      is_full_salary_continuous: false,
    },
  ],
  previous_leaves: [
    {
      type: "same_reason",
      leave_reason: "Bonding with my child after birth or placement",
      is_for_current_employer: true,
      leave_minutes: 1200,
      worked_per_week_minutes: 1200,
    },
  ],
};

// Portal claim submission with eligible employee
export const LSTBHAP1: ScenarioSpecification = {
  ...CypressScenarios.BHAP1,
  claim: {
    ...CypressScenarios.BHAP1.claim,
    label: "PortalClaimSubmit",
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
      ...employerResponseLeavesAndBenefits,
    },
    ...otherLeavesAndBenefitsProps,
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
      ...employerResponseLeavesAndBenefits,
    },
    ...otherLeavesAndBenefitsProps,
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
