import path from "path";
import { ScenarioSpecification } from "../generation/Scenario";
import * as CypressScenarios from "./cypress";
import { ClaimSpecification, EmployerResponseSpec } from "../generation/Claim";
import shuffle from "../../src/generation/shuffle";

/**
 * Load & Stress Testing Scenarios.
 *
 */

const otherLeavesAndBenefitsProps: Pick<
  ClaimSpecification,
  | "other_incomes"
  | "employer_benefits"
  | "previous_leaves_other_reason"
  | "previous_leaves_same_reason"
  | "concurrent_leave"
> = {
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

const selectRandomFile = (): string => {
  type FileSizeRanges = "<4.8" | "4.8MB-6.8MB" | "7MB-10MB";
  const wheel: Array<FileSizeRanges> =
    process.env.USE_LARGE_DOCUMENT_UPLOADS === "true"
      ? [...Array(70).fill("4.8MB-6.8MB"), ...Array(30).fill("7MB-10MB")]
      : [
          ...Array(80).fill("<4.8"),
          ...Array(12).fill("4.8MB-6.8MB"),
          ...Array(8).fill("7MB-10MB"),
        ];
  const range = wheel[Math.floor(Math.random() * wheel.length)];
  const filesMap: Record<FileSizeRanges, string[]> = {
    "<4.8": ["150KB.pdf", "1MB.jpg", "2.7MB.png", "4.5MB.pdf"],
    "4.8MB-6.8MB": ["5MB.pdf", "6MB.pdf"],
    "7MB-10MB": ["7MB.pdf", "8MB.pdf", "9.4MB.pdf"],
  };
  const filesInRanges = filesMap[range];
  const file = shuffle(filesInRanges)[0];
  return path.join("forms", "lst", file);
};
export const LSTOLB1: ScenarioSpecification = {
  ...CypressScenarios.BHAP1,
  claim: {
    ...CypressScenarios.BHAP1.claim,
    label: "PortalClaimSubmit - Other Leaves/Benefits",
    docs: {
      FOSTERPLACEMENT: {
        filename: selectRandomFile,
      },
      MASSID: {
        filename: selectRandomFile,
      },
    },
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
      ...employerResponseLeavesAndBenefits,
    },
    ...otherLeavesAndBenefitsProps,
  },
};

// Portal claim submission with eligible employee
export const LSTBHAP1: ScenarioSpecification = {
  ...CypressScenarios.BHAP1,
  claim: {
    ...CypressScenarios.BHAP1.claim,
    label: "PortalClaimSubmit - Bonding",
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
    },
    docs: {
      FOSTERPLACEMENT: {
        filename: selectRandomFile,
      },
      MASSID: {
        filename: selectRandomFile,
      },
    },
  },
};

export const LSTCHAP1: ScenarioSpecification = {
  employee: {
    wages: "eligible",
    mass_id: true,
  },
  claim: {
    label: "PortalClaimSubmit - Caring",
    reason: "Care for a Family Member",
    work_pattern_spec: "0,720,0,720,0,720,0",
    docs: {
      MASSID: {
        filename: selectRandomFile,
      },
      CARING: {
        filename: selectRandomFile,
      },
    },
    shortClaim: true,
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
    },
    is_withholding_tax: true,
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
  employee: { mass_id: true, wages: "ineligible" },
  claim: {
    label: "FineosClaimSubmit",
    shortClaim: true,
    reason: "Child Bonding",
    reason_qualifier: "Foster Care",
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Deny",
    },
    docs: {
      MASSID: {},
      FOSTERPLACEMENT: {},
    },
  },
};
