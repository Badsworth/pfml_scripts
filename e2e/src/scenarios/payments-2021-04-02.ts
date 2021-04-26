// Unhappy path:
import { ScenarioSpecification } from "../generation/Scenario";
import { addWeeks } from "date-fns";

const addresses = {
  valid: {
    city: "Quincy",
    line_1: "47 Washington St",
    state: "MA",
    zip: "02169",
  },
  onetoonecorrection: {
    city: "Quincy",
    line_1: "47 Washington",
    state: "MA",
    zip: "02169",
  },
  invalid: {
    city: "Jennytown",
    line_1: "444 Super Lane",
    state: "MA",
    zip: "10000",
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
};

export const PMT1: ScenarioSpecification = {
  employee: { wages: 30000, metadata: { prenoted: "no" } },
  claim: {
    label: "PMT1",
    reason: "Child Bonding",
    reason_qualifier: "Newborn",
    has_continuous_leave_periods: true,
    leave_dates: [addWeeks(new Date(), -2), addWeeks(new Date(), 4)],
    address: addresses.valid,
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
    metadata: { postSubmit: "APPROVE" },
  },
};

export const PMT2: ScenarioSpecification = {
  employee: { wages: 30000, metadata: { prenoted: "no" } },
  claim: {
    label: "PMT2",
    reason: "Child Bonding",
    reason_qualifier: "Newborn",
    has_continuous_leave_periods: true,
    leave_dates: [addWeeks(new Date(), -4), addWeeks(new Date(), 4)],
    address: addresses.valid,
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
    metadata: { postSubmit: "APPROVE" },
  },
};

export const PMT3: ScenarioSpecification = {
  // Note: For prenoted employees, we'll use a picker function instead of the regular spec.
  // This allows us to manually mark some employees as prenoted, then use them.
  employee: { wages: 30000, metadata: { prenoted: "yes" } },
  claim: {
    label: "PMT3",
    reason: "Child Bonding",
    reason_qualifier: "Newborn",
    has_continuous_leave_periods: true,
    leave_dates: [addWeeks(new Date(), -2), addWeeks(new Date(), 4)],
    address: addresses.valid,
    payment: payments.eftvalid,
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
    metadata: { postSubmit: "APPROVE" },
  },
};

export const PMT4: ScenarioSpecification = {
  // Note: For prenoted employees, we'll use a picker function instead of the regular spec.
  // This allows us to manually mark some employees as prenoted, then use them.
  employee: { wages: 30000, metadata: { prenoted: "pending" } },
  claim: {
    label: "PMT4",
    reason: "Child Bonding",
    reason_qualifier: "Newborn",
    has_continuous_leave_periods: true,
    leave_dates: [addWeeks(new Date(), -2), addWeeks(new Date(), 4)],
    address: addresses.valid,
    payment: payments.eftvalid,
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
    metadata: { postSubmit: "APPROVE" },
  },
};

// ACH payment with no prenote request
export const PMT5: ScenarioSpecification = {
  // Note: For prenoted employees, we'll use a picker function instead of the regular spec.
  // This allows us to manually mark some employees as prenoted, then use them.
  employee: { wages: 30000, metadata: { prenoted: "no" } },
  claim: {
    label: "PMT5",
    reason: "Child Bonding",
    reason_qualifier: "Newborn",
    has_continuous_leave_periods: true,
    leave_dates: [addWeeks(new Date(), -2), addWeeks(new Date(), 4)],
    address: addresses.valid,
    payment: payments.eftvalid,
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
    metadata: { postSubmit: "APPROVE" },
  },
};

// Family leave claim payment(s)
export const PMT6: ScenarioSpecification = {
  employee: { wages: 30000, metadata: { prenoted: "yes" } },
  claim: {
    label: "PMT6",
    reason: "Child Bonding",
    reason_qualifier: "Newborn",
    has_continuous_leave_periods: true,
    leave_dates: [addWeeks(new Date(), -2), addWeeks(new Date(), 4)],
    address: addresses.valid,
    payment: payments.eftvalid,
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
    metadata: { postSubmit: "APPROVE" },
  },
};

// Medical leave claim payment(s)
export const PMT7: ScenarioSpecification = {
  employee: { wages: 30000, metadata: { prenoted: "no" } },
  claim: {
    label: "PMT7",
    reason: "Serious Health Condition - Employee",
    has_continuous_leave_periods: true,
    leave_dates: [addWeeks(new Date(), -2), addWeeks(new Date(), 4)],
    address: addresses.valid,
    payment: payments.check,
    docs: {
      HCP: {},
      MASSID: {},
    },
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
      fraud: "No",
    },
    metadata: { postSubmit: "APPROVE" },
  },
};

// Prenote request – valid bank account information
export const PRENOTE1: ScenarioSpecification = {
  employee: { wages: 30000, metadata: { prenoted: "no" } },
  claim: {
    label: "PRENOTE1",
    reason: "Serious Health Condition - Employee",
    has_continuous_leave_periods: true,
    leave_dates: [addWeeks(new Date(), 1), addWeeks(new Date(), 4)],
    address: addresses.valid,
    payment: payments.eftvalid,
    docs: {
      HCP: {},
      MASSID: {},
    },
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
      fraud: "No",
    },
    metadata: { postSubmit: "APPROVEDOCS" },
  },
};

// Prenote request – invalid bank routing number, valid account number
// export const PRENOTE2: ScenarioSpecification = {
//   employee: { wages: 30000, metadata: { prenoted: "no" } },
//   claim: {
//     label: "PRENOTE2",
//     reason: "Serious Health Condition - Employee",
//     has_continuous_leave_periods: true,
//     leave_dates: [addWeeks(new Date(), 1), addWeeks(new Date(), 4)],
//     address: addresses.valid,
//     payment: payments.eftinvalid,
//     docs: {
//       HCP: {},
//       MASSID: {},
//     },
//     employerResponse: {
//       hours_worked_per_week: 40,
//       employer_decision: "Approve",
//       fraud: "No",
//     },
//     metadata: { postSubmit: "APPROVEDOCS" },
//   },
// };

// Invalid Address
export const PRENOTE5: ScenarioSpecification = {
  employee: { wages: 30000, metadata: { prenoted: "no" } },
  claim: {
    label: "PRENOTE5",
    reason: "Serious Health Condition - Employee",
    has_continuous_leave_periods: true,
    leave_dates: [addWeeks(new Date(), 1), addWeeks(new Date(), 4)],
    address: addresses.invalid,
    payment: payments.eftvalid,
    docs: {
      HCP: {},
      MASSID: {},
    },
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
      fraud: "No",
    },
    metadata: { postSubmit: "APPROVEDOCS" },
  },
};

// Valid address for check payment – no correction needed from Experian
export const ADDRESS1: ScenarioSpecification = {
  employee: { wages: 30000, metadata: { prenoted: "no" } },
  claim: {
    label: "ADDRESS1",
    reason: "Serious Health Condition - Employee",
    has_continuous_leave_periods: true,
    leave_dates: [addWeeks(new Date(), -2), addWeeks(new Date(), 4)],
    address: addresses.valid,
    payment: payments.check,
    docs: {
      HCP: {},
      MASSID: {},
    },
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
      fraud: "No",
    },
    metadata: { postSubmit: "APPROVE" },
  },
};

// Valid address for check payment – one for one correction provided from Experian (we removed "st" in address)
export const ADDRESS2: ScenarioSpecification = {
  employee: { wages: 30000, metadata: { prenoted: "no" } },
  claim: {
    label: "ADDRESS2",
    reason: "Serious Health Condition - Employee",
    has_continuous_leave_periods: true,
    leave_dates: [addWeeks(new Date(), -2), addWeeks(new Date(), 4)],
    address: addresses.onetoonecorrection,
    payment: payments.check,
    docs: {
      HCP: {},
      MASSID: {},
    },
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
      fraud: "No",
    },
    metadata: { postSubmit: "APPROVE" },
  },
};

export const ADDRESS3: ScenarioSpecification = {
  employee: { wages: 30000, metadata: { prenoted: "no" } },
  claim: {
    label: "ADDRESS3",
    reason: "Serious Health Condition - Employee",
    has_continuous_leave_periods: true,
    leave_dates: [addWeeks(new Date(), -2), addWeeks(new Date(), 4)],
    address: addresses.invalid,
    payment: payments.check,
    docs: {
      HCP: {},
      MASSID: {},
    },
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
      fraud: "No",
    },
    metadata: { postSubmit: "APPROVE" },
  },
};

// Valid address for ACH payment – no correction needed from Experian
export const ADDRESS5: ScenarioSpecification = {
  employee: { wages: 30000, metadata: { prenoted: "yes" } },
  claim: {
    label: "ADDRESS5",
    reason: "Serious Health Condition - Employee",
    has_continuous_leave_periods: true,
    leave_dates: [addWeeks(new Date(), -2), addWeeks(new Date(), 4)],
    address: addresses.valid,
    payment: payments.eftvalid,
    docs: {
      HCP: {},
      MASSID: {},
    },
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
      fraud: "No",
    },
    metadata: { postSubmit: "APPROVE" },
  },
};

// Valid address for ACH payment – one for one correction provided from Experian
// Valid address for ACH payment – no correction needed from Experian
export const ADDRESS6: ScenarioSpecification = {
  employee: { wages: 30000, metadata: { prenoted: "yes" } },
  claim: {
    label: "ADDRESS6",
    reason: "Serious Health Condition - Employee",
    has_continuous_leave_periods: true,
    leave_dates: [addWeeks(new Date(), -2), addWeeks(new Date(), 4)],
    address: addresses.onetoonecorrection,
    payment: payments.eftvalid,
    docs: {
      HCP: {},
      MASSID: {},
    },
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
      fraud: "No",
    },
    metadata: { postSubmit: "APPROVE" },
  },
};
// Valid address for ACH payment – no correction needed from Experian
export const ADDRESS7: ScenarioSpecification = {
  employee: { wages: 30000, metadata: { prenoted: "yes" } },
  claim: {
    label: "ADDRESS7",
    reason: "Serious Health Condition - Employee",
    has_continuous_leave_periods: true,
    leave_dates: [addWeeks(new Date(), -2), addWeeks(new Date(), 4)],
    address: addresses.invalid,
    payment: payments.eftvalid,
    docs: {
      HCP: {},
      MASSID: {},
    },
    employerResponse: {
      hours_worked_per_week: 40,
      employer_decision: "Approve",
      fraud: "No",
    },
    metadata: { postSubmit: "APPROVE" },
  },
};
