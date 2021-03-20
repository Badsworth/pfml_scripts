import { parseISO } from "date-fns";
import { ScenarioSpecification } from "../generation/Scenario";

// Mixed decision variable work pattern
export const MDV: ScenarioSpecification = {
  employee: {
    mass_id: true,
    wages: "eligible",
  },
  claim: {
    label: "MDV",
    reason: "Child Bonding",
    reason_qualifier: "Newborn",
    work_pattern_spec: "variable",
    bondingDate: "past",
    has_continuous_leave_periods: true,
    leave_dates: [parseISO("2021-03-01"), parseISO("2021-06-07")],
    docs: {},
  },
};

// Mixed decision fixed work pattern
export const MDF: ScenarioSpecification = {
  employee: {
    mass_id: true,
    wages: "eligible",
  },
  claim: {
    label: "MDF",
    reason: "Child Bonding",
    reason_qualifier: "Newborn",
    bondingDate: "past",
    has_continuous_leave_periods: true,
    leave_dates: [parseISO("2021-03-01"), parseISO("2021-06-07")],
    docs: {},
  },
};
