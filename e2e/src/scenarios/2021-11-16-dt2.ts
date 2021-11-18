import {MedicalClaim, ScenarioSpecification} from "../generation/Scenario";
import {addDays, startOfWeek} from "date-fns";

export const FSTRUE1: ScenarioSpecification<MedicalClaim> = {
  employee: { wages: "eligible" },
  claim: {
    reason: "Serious Health Condition - Employee",
    label: "FSTRUE1",
    leave_dates: [
      startOfWeek(addDays(new Date(), 53)), // dates 1/10/22 - 1/30/22
      startOfWeek(addDays(new Date(), 74)),
    ],
    work_pattern_spec: "standard",
    is_withholding_tax: true,
    has_continuous_leave_periods: true,
    docs: { HCP: {}, MASSID: {} },
    metadata: { postSubmit: "APPROVE" },
  },
};

export const FSTRUE2: ScenarioSpecification<MedicalClaim> = {
  employee: { wages: "eligible" },
  claim: {
    reason: "Serious Health Condition - Employee",
    label: "FSTRUE2",
    leave_dates: [
      startOfWeek(addDays(new Date(), 53)), // dates 1/4/22 - 2/15/22
      startOfWeek(addDays(new Date(), 90)),
    ],
    work_pattern_spec: "standard",
    is_withholding_tax: true,
    has_continuous_leave_periods: true,
    docs: { HCP: {}, MASSID: {} },
    metadata: { postSubmit: "APPROVE" },
  },
};

export const FSTRUE3: ScenarioSpecification<MedicalClaim> = {
  employee: { wages: "eligible" },
  claim: {
    reason: "Serious Health Condition - Employee",
    label: "FSTRUE3",
    leave_dates: [
      startOfWeek(addDays(new Date(), 23)), // dates 12/10/21 - 12/30/21
      startOfWeek(addDays(new Date(), 43)),
    ],
    work_pattern_spec: "standard",
    is_withholding_tax: true,
    has_continuous_leave_periods: true,
    docs: { HCP: {}, MASSID: {} },
    metadata: { postSubmit: "APPROVE" },
  },
};

export const FSTRUE4: ScenarioSpecification<MedicalClaim> = {
  employee: { wages: "eligible" },
  claim: {
    reason: "Serious Health Condition - Employee",
    label: "FSTRUE4",
    leave_dates: [
      startOfWeek(addDays(new Date(), 38)), // dates 12/25/21 - 1/5/22
      startOfWeek(addDays(new Date(), 49)),
    ],
    work_pattern_spec: "standard",
    is_withholding_tax: true,
    has_continuous_leave_periods: true,
    docs: { HCP: {}, MASSID: {} },
    metadata: { postSubmit: "APPROVE" },
  },
};

export const FSTRUE5: ScenarioSpecification<MedicalClaim> = {
  employee: { wages: 90000 },
  claim: {
    reason: "Serious Health Condition - Employee",
    label: "FSTRUE5",
    leave_dates: [
      startOfWeek(addDays(new Date(), 49)), // dates 1/5/21 - 2/15/22
      startOfWeek(addDays(new Date(), 90)),
    ],
    work_pattern_spec: "standard",
    is_withholding_tax: true,
    has_continuous_leave_periods: true,
    docs: { HCP: {}, MASSID: {} },
    metadata: { postSubmit: "APPROVE" },
  },
};

export const FSTRUE6: ScenarioSpecification<MedicalClaim> = {
  employee: { wages: 90000 },
  claim: {
    reason: "Serious Health Condition - Employee",
    label: "FSTRUE6",
    leave_dates: [
      startOfWeek(addDays(new Date(), 48)), // dates 1/4/21 - 2/10/22
      startOfWeek(addDays(new Date(), 85)),
    ],
    work_pattern_spec: "standard",
    is_withholding_tax: true,
    has_continuous_leave_periods: true,
    docs: { HCP: {}, MASSID: {} },
    metadata: { postSubmit: "APPROVE" },
  },
};

export const FSTRUE7: ScenarioSpecification<MedicalClaim> = {
  employee: { wages: "eligible" },
  claim: {
    reason: "Serious Health Condition - Employee",
    label: "FSTRUE7",
    leave_dates: [
      startOfWeek(addDays(new Date(), 48)), // dates 1/4/21 - 2/15/22
      startOfWeek(addDays(new Date(), 90)),
    ],
    work_pattern_spec: "standard",
    is_withholding_tax: true,
    has_continuous_leave_periods: true,
    docs: { HCP: {}, MASSID: {} },
    metadata: { postSubmit: "APPROVE" },
  },
};

export const FSTRUE8: ScenarioSpecification<MedicalClaim> = {
  employee: { wages: 90000 },
  claim: {
    reason: "Serious Health Condition - Employee",
    label: "FSTRUE8",
    leave_dates: [
      startOfWeek(addDays(new Date(), 49)), // dates 1/5/21 - 1/30/22
      startOfWeek(addDays(new Date(), 74)),
    ],
    work_pattern_spec: "standard",
    is_withholding_tax: true,
    has_continuous_leave_periods: true,
    docs: { HCP: {}, MASSID: {} },
    metadata: { postSubmit: "APPROVE" },
  },
};

export const FSTRUE9: ScenarioSpecification<MedicalClaim> = {
  employee: { wages: "eligible" },
  claim: {
    reason: "Serious Health Condition - Employee",
    label: "FSTRUE9",
    leave_dates: [
      startOfWeek(addDays(new Date(), 48)), // dates 1/4/21 - 2/15/22
      startOfWeek(addDays(new Date(), 90)),
    ],
    work_pattern_spec: "standard",
    is_withholding_tax: false,
    has_continuous_leave_periods: true,
    docs: { HCP: {}, MASSID: {} },
    metadata: { postSubmit: "APPROVE" },
  },
};

export const FSTRUE10: ScenarioSpecification<MedicalClaim> = {
  employee: { wages: "eligible" },
  claim: {
    reason: "Serious Health Condition - Employee",
    label: "FSTRUE10",
    leave_dates: [
      startOfWeek(addDays(new Date(), 49)), // dates 1/5/21 - 1/30/22
      startOfWeek(addDays(new Date(), 74)),
    ],
    work_pattern_spec: "standard",
    is_withholding_tax: false,
    has_continuous_leave_periods: true,
    docs: { HCP: {}, MASSID: {} },
    metadata: { postSubmit: "APPROVE" },
  },
};
