import { ScenarioSpecification } from "../generation/Scenario";
import { parseISO } from "date-fns";

const error_tolerance_claim_amount = 1.20;

export const DT4_APRIL_A: ScenarioSpecification =
  {
    employee: { mass_id: true, wages: "eligible" },
    claim: {
      label: "DT4_APRIL_A",
      work_pattern_spec: "standard",
      intermittent_leave_spec: {
        duration: 3,
        duration_basis: "Days",
      },
      reason: "Serious Health Condition - Employee",
      leave_dates: [parseISO("2022-03-13"), parseISO("2022-05-01")],
      is_withholding_tax: false,
      docs: {
        MASSID: {},
        HCP: {},
      },
      metadata: {
        postSubmit: "APPROVE",
        amount: 4 * error_tolerance_claim_amount,
      },
    },
  };
