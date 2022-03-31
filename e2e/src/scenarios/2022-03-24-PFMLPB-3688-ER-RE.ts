import { ScenarioSpecification } from "../generation/Scenario";
import { addWeeks } from "date-fns";

const addresses = {
  valid1: {
    city: "Norwood",
    line_1: "187 Walpole St",
    state: "MA",
    zip: "02062-3230",
  },
  valid2: {
    city: "Walpole",
    line_1: "30 Front St",
    state: "MA",
    zip: "02081-2802",
  },
  valid3: {
    city: "Worcester",
    line_1: "27 Mount Ave",
    state: "MA",
    zip: "01606-1927",
  },
  valid4: {
    city: "Webster",
    line_1: "33 Joyce St",
    state: "MA",
    zip: "01570-2716",
  },
  invalid: {
    city: "Jennytown",
    line_1: "444 Super St",
    state: "MA",
    zip: "01000",
  },
};

const payments = {
  check: {
    payment_method: "Check" as const,
  },
  eftvalid: {
    payment_method: "Elec Funds Transfer" as const,
    routing_number: "221172186",
    account_number: "014901507",
    bank_account_type: "Checking" as const,
  },
  eftinvalid: {
    payment_method: "Elec Funds Transfer" as const,
    routing_number: "555555855",
    account_number: "123456789",
    bank_account_type: "Checking" as const,
  },
};

const RE_PYMT1: ScenarioSpecification = {
  employee: { wages: 90000, metadata: { prenoted: "yes" } },
  claim: {
    label: "RE_PYMT1",
    reason: "Child Bonding",
    reason_qualifier: "Newborn",
    has_continuous_leave_periods: true,
    leave_dates: [addWeeks(new Date(), -3), addWeeks(new Date(), 2)],
    address: addresses.invalid,
    payment: payments.check,
    bondingDate: "past",
    docs: {
      MASSID: {},
      BIRTHCERTIFICATE: {},
    },
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
      fraud: "No",
    },
    metadata: { postSubmit: "ADDERREIMBURSEMENT", employerReAmount: 1084.31 },
  },
};

const RE_PYMT2: ScenarioSpecification = {
  employee: { wages: 60000, metadata: { prenoted: "yes" } },
  claim: {
    label: "RE_PYMT2",
    reason: "Serious Health Condition - Employee",
    has_continuous_leave_periods: true,
    leave_dates: [addWeeks(new Date(), -3), addWeeks(new Date(), 2)],
    address: addresses.valid1,
    payment: payments.check,
    docs: {
      MASSID: {},
      HCP: {},
    },
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
      fraud: "No",
    },
    is_withholding_tax: false,
    metadata: { postSubmit: "ADDERREIMBURSEMENT", employerReAmount: 500 },
  },
};

const RE_PYMT3: ScenarioSpecification = {
  employee: { wages: 30000, metadata: { prenoted: "yes" } },
  claim: {
    label: "RE_PYMT3",
    reason: "Care for a Family Member",
    has_continuous_leave_periods: true,
    leave_dates: [addWeeks(new Date(), -4), addWeeks(new Date(), 2)],
    address: addresses.valid2,
    payment: payments.check,
    docs: {
      MASSID: {},
      CARING: {},
    },
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
      fraud: "No",
    },
    is_withholding_tax: true,
    metadata: { postSubmit: "ADDERREIMBURSEMENT", employerReAmount: 300 },
  },
};

const RE_PYMT4: ScenarioSpecification = {
  employee: { wages: 60000, metadata: { prenoted: "yes" } },
  claim: {
    label: "RE_PYMT4",
    reason: "Pregnancy/Maternity",
    has_continuous_leave_periods: true,
    leave_dates: [addWeeks(new Date(), -3), addWeeks(new Date(), 2)],
    address: addresses.valid3,
    payment: payments.eftvalid,
    docs: {
      MASSID: {},
      PREGNANCY_MATERNITY_FORM: {},
    },
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
      fraud: "No",
    },
    is_withholding_tax: false,
    metadata: { postSubmit: "ADDERREIMBURSEMENT", employerReAmount: 500 },
  },
};

const RE_PYMT5: ScenarioSpecification = {
  employee: { wages: 30000, metadata: { prenoted: "yes" } },
  claim: {
    label: "RE_PYMT5",
    reason: "Serious Health Condition - Employee",
    has_continuous_leave_periods: true,
    leave_dates: [addWeeks(new Date(), -3), addWeeks(new Date(), 2)],
    address: addresses.valid4,
    payment: payments.eftvalid,
    docs: {
      MASSID: {},
      HCP: {},
    },
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
      fraud: "No",
    },
    is_withholding_tax: true,
    metadata: { postSubmit: "ADDERREIMBURSEMENT", employerReAmount: 300 },
  },
};

const RE_PYMT6: ScenarioSpecification = {
  employee: { wages: 90000, metadata: { prenoted: "yes" } },
  claim: {
    label: "RE_PYMT6",
    reason: "Child Bonding",
    reason_qualifier: "Newborn",
    has_continuous_leave_periods: true,
    leave_dates: [addWeeks(new Date(), -4), addWeeks(new Date(), 2)],
    address: addresses.invalid,
    payment: payments.check,
    bondingDate: "past",
    docs: {
      MASSID: {},
      BIRTHCERTIFICATE: {},
    },
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
      fraud: "No",
    },
    metadata: { postSubmit: "ADDERREIMBURSEMENT", employerReAmount: 1084.31 },
  },
};

const RE_PYMT7: ScenarioSpecification = {
  employee: { wages: 60000, metadata: { prenoted: "yes" } },
  claim: {
    label: "RE_PYMT7",
    reason: "Child Bonding",
    reason_qualifier: "Newborn",
    has_continuous_leave_periods: true,
    leave_dates: [addWeeks(new Date(), -3), addWeeks(new Date(), 2)],
    address: addresses.valid1,
    payment: payments.check,
    bondingDate: "past",
    docs: {
      MASSID: {},
      BIRTHCERTIFICATE: {},
    },
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
      fraud: "No",
    },
    is_withholding_tax: false,
    metadata: { postSubmit: "ADDERREIMBURSEMENT", employerReAmount: 500 },
  },
};

const RE_PYMT8: ScenarioSpecification = {
  employee: { wages: 30000, metadata: { prenoted: "yes" } },
  claim: {
    label: "RE_PYMT8",
    reason: "Care for a Family Member",
    has_continuous_leave_periods: true,
    leave_dates: [addWeeks(new Date(), -4), addWeeks(new Date(), 2)],
    address: addresses.invalid,
    payment: payments.check,
    docs: {
      MASSID: {},
      CARING: {},
    },
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
      fraud: "No",
    },
    is_withholding_tax: true,
    metadata: { postSubmit: "ADDERREIMBURSEMENT", employerReAmount: 300 },
  },
};

const RE_PYMT9: ScenarioSpecification = {
  employee: { wages: 60000, metadata: { prenoted: "yes" } },
  claim: {
    label: "RE_PYMT9",
    reason: "Pregnancy/Maternity",
    has_continuous_leave_periods: true,
    leave_dates: [addWeeks(new Date(), -3), addWeeks(new Date(), 2)],
    address: addresses.invalid,
    payment: payments.check,
    docs: {
      MASSID: {},
      PREGNANCY_MATERNITY_FORM: {},
    },
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
      fraud: "No",
    },
    is_withholding_tax: true,
    metadata: { postSubmit: "ADDERREIMBURSEMENT", employerReAmount: 500 },
  },
};

const RE_PYMT10: ScenarioSpecification = {
  employee: { wages: 30000, metadata: { prenoted: "yes" } },
  claim: {
    label: "RE_PYMT10",
    reason: "Serious Health Condition - Employee",
    has_continuous_leave_periods: true,
    leave_dates: [addWeeks(new Date(), -4), addWeeks(new Date(), 2)],
    address: addresses.invalid,
    payment: payments.eftvalid,
    docs: {
      MASSID: {},
      HCP: {},
    },
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
      fraud: "No",
    },
    is_withholding_tax: true,
    metadata: { postSubmit: "ADDERREIMBURSEMENT", employerReAmount: 300 },
  },
};

export const scenariosWithValidEmployerAddress = [
  RE_PYMT1,
  RE_PYMT2,
  RE_PYMT3,
  RE_PYMT4,
  RE_PYMT5,
  RE_PYMT8,
  RE_PYMT10,
];
export const scenariosWithInvalidEmployerAdress = [
  RE_PYMT6,
  RE_PYMT7,
  RE_PYMT9,
];
