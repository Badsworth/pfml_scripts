import { scenario } from "../simulate";

// Additional scenarios for integration testing that should not be included in LST or BizSim
export const BHAP8 = scenario("BHAP8", {
  reason: "Child Bonding",
  reason_qualifier: "Foster Care",
  residence: "MA-proofed",
  docs: {
    HCP: {},
    MASSID: {},
  },
  work_pattern_spec: "standard",
  reduced_leave_spec: "0,240,240,240,240,240,0",
});

export const BHAP9 = scenario("BHAP9", {
  reason: "Child Bonding",
  reason_qualifier: "Foster Care",
  residence: "MA-proofed",
  docs: {
    HCP: {},
    MASSID: {},
  },
  has_intermittent_leave_periods: true,
});

// Mailed HCP, MA Resident, Bonding
export const BGBM1 = scenario("MGBM1", {
  reason: "Child Bonding",
  reason_qualifier: "Foster Care",
  residence: "MA-proofed",
  docs: {
    HCP: { mailed: true },
    MASSID: {},
  },
});

export const MBIRTH = scenario("MBIRTH", {
  reason: "Serious Health Condition - Employee",
  residence: "MA-proofed",
  pregnant_or_recent_birth: true,
  docs: {
    HCP: {},
    MASSID: {},
  },
});

// Happy Path Foster (ID proofing)
export const BHAP10ID = scenario("BHAP10ID", {
  reason: "Child Bonding",
  reason_qualifier: "Foster Care",
  residence: "MA-proofed",
  id_proof: true,
  id_check: "valid",
  docs: {
    MASSID: {},
    FOSTERPLACEMENT: {},
  },
});

export const BHAP11ID = scenario("BHAP11ID", {
  reason: "Child Bonding",
  reason_qualifier: "Foster Care",
  residence: "MA-proofed",
  id_proof: true,
  id_check: "fraud",
  docs: {
    MASSID: {},
    FOSTERPLACEMENT: {},
  },
});

export const BHAP12ID = scenario("BHAP12ID", {
  reason: "Child Bonding",
  reason_qualifier: "Foster Care",
  residence: "MA-proofed",
  id_proof: true,
  id_check: "invalid",
  docs: {
    MASSID: {},
    FOSTERPLACEMENT: {},
  },
});

export const BHAP13ID = scenario("BHAP13ID", {
  reason: "Child Bonding",
  reason_qualifier: "Foster Care",
  residence: "MA-proofed",
  id_proof: true,
  id_check: "mismatch",
  docs: {
    MASSID: {},
    FOSTERPLACEMENT: {},
  },
});

export const DHAP1 = scenario("DHAP1", {
  reason: "Child Bonding",
  reason_qualifier: "Foster Care",
  residence: "MA-proofed",
  docs: {},
});
