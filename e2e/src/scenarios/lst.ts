import path from "path";
import { ScenarioSpecification } from "../generation/Scenario";
import * as CypressScenarios from "./cypress";
import { ClaimSpecification, EmployerResponseSpec } from "../generation/Claim";

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

const getDocPath = (filename: string) => path.join("forms", "lst", filename);

export const LSTOLB1_150KB: ScenarioSpecification = {
  ...CypressScenarios.BHAP1,
  claim: {
    ...CypressScenarios.BHAP1.claim,
    label: "PortalClaimSubmit - Other Leaves/Benefits  - 150KB file size",
    docs: {
      FOSTERPLACEMENT: {
        filename: getDocPath("150KB.pdf"),
      },
      MASSID: {
        filename: getDocPath("150KB.pdf"),
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
export const LSTBHAP_1MB: ScenarioSpecification = {
  ...CypressScenarios.BHAP1,
  claim: {
    ...CypressScenarios.BHAP1.claim,
    label: "PortalClaimSubmit - Bonding - 1MB file size",
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
    },
    docs: {
      FOSTERPLACEMENT: {
        filename: getDocPath("1MB.jpg"),
      },
      MASSID: {
        filename: getDocPath("1MB.jpg"),
      },
    },
  },
};

export const LSTCHAP1_2MB: ScenarioSpecification = {
  employee: {
    wages: "eligible",
    mass_id: true,
  },
  claim: {
    label: "PortalClaimSubmit - Caring - 2.7MB file sizes",
    reason: "Care for a Family Member",
    work_pattern_spec: "0,720,0,720,0,720,0",
    docs: {
      MASSID: {
        filename: getDocPath("2.7MB.png"),
      },
      CARING: {
        filename: getDocPath("2.7MB.png"),
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

export const LSTOLB1_4MB: ScenarioSpecification = {
  ...CypressScenarios.BHAP1,
  claim: {
    ...CypressScenarios.BHAP1.claim,
    label: "PortalClaimSubmit - Other Leaves/Benefits  - 4.5MB file size",
    docs: {
      FOSTERPLACEMENT: {
        filename: getDocPath("4.5MB.pdf"),
      },
      MASSID: {
        filename: getDocPath("4.5MB.pdf"),
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
export const LSTBHAP_5MB: ScenarioSpecification = {
  ...CypressScenarios.BHAP1,
  claim: {
    ...CypressScenarios.BHAP1.claim,
    label: "PortalClaimSubmit - Bonding - 5MB file size",
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
    },
    docs: {
      FOSTERPLACEMENT: {
        filename: getDocPath("5MB"),
      },
      MASSID: {
        filename: getDocPath("5MB"),
      },
    },
  },
};

export const LSTCHAP1_6MB: ScenarioSpecification = {
  employee: {
    wages: "eligible",
    mass_id: true,
  },
  claim: {
    label: "PortalClaimSubmit - Caring - 6MB file sizes",
    reason: "Care for a Family Member",
    work_pattern_spec: "0,720,0,720,0,720,0",
    docs: {
      MASSID: {
        filename: getDocPath("6MB.pdf"),
      },
      CARING: {
        filename: getDocPath("6MB.pdf"),
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

export const LSTOLB1_7MB: ScenarioSpecification = {
  ...CypressScenarios.BHAP1,
  claim: {
    ...CypressScenarios.BHAP1.claim,
    label: "PortalClaimSubmit - Other Leaves/Benefits  - 7MB file size",
    docs: {
      FOSTERPLACEMENT: {
        filename: getDocPath("7MB.pdf"),
      },
      MASSID: {
        filename: getDocPath("7MB.pdf"),
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
export const LSTBHAP_8MB: ScenarioSpecification = {
  ...CypressScenarios.BHAP1,
  claim: {
    ...CypressScenarios.BHAP1.claim,
    label: "PortalClaimSubmit - Bonding - 8MB file size",
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
    },
    docs: {
      FOSTERPLACEMENT: {
        filename: getDocPath("8MB"),
      },
      MASSID: {
        filename: getDocPath("8MB"),
      },
    },
  },
};

export const LSTCHAP1_9MB: ScenarioSpecification = {
  employee: {
    wages: "eligible",
    mass_id: true,
  },
  claim: {
    label: "PortalClaimSubmit - Caring - 9.4MB file sizes",
    reason: "Care for a Family Member",
    work_pattern_spec: "0,720,0,720,0,720,0",
    docs: {
      MASSID: {
        filename: getDocPath("9.4MB"),
      },
      CARING: {
        filename: getDocPath("9.4MB"),
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
