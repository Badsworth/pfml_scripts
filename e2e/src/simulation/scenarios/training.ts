import { chance, scenario } from "../simulate";

// Financially Ineligible.  10 needed
// Happy path denial due to financial eligibility.
export const INELIGIBLE1 = scenario("INELIGIBLE1", {
  reason: "Child Bonding",
  reason_qualifier: "Newborn",
  residence: "MA-proofed",
  financiallyIneligible: true,
  bondingDate: "past",
  docs: {
    MASSID: {},
    BIRTHCERTIFICATE: {},
  },
});
export const INELIGIBLE2 = scenario("INELIGIBLE2", {
  reason: "Child Bonding",
  reason_qualifier: "Adoption",
  residence: "MA-proofed",
  financiallyIneligible: true,
  bondingDate: "past",
  docs: {
    MASSID: {},
    ADOPTIONCERT: {},
  },
});
const INELIGIBLE = chance([
  [1, INELIGIBLE1],
  [1, INELIGIBLE2],
]);

// OK Documentation
export const VALID1 = scenario("VALID1", {
  reason: "Child Bonding",
  reason_qualifier: "Newborn",
  residence: "MA-proofed",
  bondingDate: "past",
  docs: {
    MASSID: {},
    BIRTHCERTIFICATE: {},
  },
});
export const VALID2 = scenario("VALID2", {
  reason: "Child Bonding",
  reason_qualifier: "Adoption",
  residence: "MA-proofed",
  bondingDate: "past",
  docs: {
    MASSID: {},
    ADOPTIONCERT: {},
  },
});
export const VALID3 = scenario("VALID3", {
  reason: "Child Bonding",
  reason_qualifier: "Foster Care",
  residence: "MA-proofed",
  bondingDate: "past",
  docs: {
    MASSID: {},
    FOSTERPLACEMENT: {},
  },
});

const VALID = chance([
  [1, VALID1],
  [1, VALID2],
  [1, VALID3],
]);

// Bad Documentation
export const INVALID1 = scenario("INVALID1", {
  reason: "Child Bonding",
  reason_qualifier: "Newborn",
  residence: "MA-proofed",
  bondingDate: "past",
  docs: {
    MASSID: {
      invalid: true,
    },
    BIRTHCERTIFICATE: {
      invalid: true,
    },
  },
});
export const INVALID2 = scenario("INVALID2", {
  reason: "Child Bonding",
  reason_qualifier: "Adoption",
  residence: "MA-proofed",
  bondingDate: "past",
  docs: {
    MASSID: {
      invalid: true,
    },
    // @todo: Need to make this have an invalid state.
    ADOPTIONCERT: {
      invalid: true,
    },
  },
});
export const INVALID3 = scenario("INVALID3", {
  reason: "Child Bonding",
  reason_qualifier: "Foster Care",
  residence: "MA-proofed",
  bondingDate: "past",
  docs: {
    MASSID: {
      invalid: true,
    },
    // @todo: Need to make this have an invalid state.
    FOSTERPLACEMENT: {
      invalid: true,
    },
  },
});

const INVALID = chance([
  [1, INVALID1],
  [1, INVALID2],
  [1, INVALID3],
]);

export default chance([
  [10, INELIGIBLE],
  [490, VALID],
  [250, INVALID],
]);
