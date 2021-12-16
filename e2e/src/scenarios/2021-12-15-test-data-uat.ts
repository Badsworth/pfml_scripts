import {MedicalClaim, PregnancyClaim, ScenarioSpecification} from "../generation/Scenario";
import {addDays, subDays, startOfWeek} from "date-fns";

// this goes in the scenario folder structure.
export const ORG1: ScenarioSpecification<MedicalClaim> = {
  employee: { wages: "eligible" },
  claim: {
    reason: "Serious Health Condition - Employee",
    label: "ORG1",
    work_pattern_spec: "standard",
    docs: { HCP: {}, MASSID: {} },
  },
};

export const ORG2: ScenarioSpecification<MedicalClaim> = {
  employee: { wages: 90000 },
  claim: {
    reason: "Serious Health Condition - Employee",
    label: "ORG2",
    work_pattern_spec: "standard",
    has_continuous_leave_periods: true,
    docs: { HCP: {}, MASSID: {} },
  },
};
