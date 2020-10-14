import { scenario, chance } from "../simulate";

export const BHAP1 = scenario("BHAP1", {
  reason: "Child Bonding",
  reason_qualifier: "Foster Care",
  residence: "MA-proofed",
  docs: {
    MASSID: {},
    // @todo: Implement document type.
    FOSTERPLACEMENT: {},
  },
});

export const BHAP2 = scenario("BHAP2", {
  reason: "Child Bonding",
  reason_qualifier: "Adoption",
  residence: "OOS",
  docs: {
    OOSID: {},
    // @todo: Implement document type.
    ADOPTIONCERT: {},
  },
});

export const BHAP3 = scenario("BHAP3", {
  reason: "Child Bonding",
  reason_qualifier: "Newborn",
  residence: "MA-proofed",
  docs: {
    MASSID: {},
    // @todo: Implement document type.
    PREBIRTH: {},
  },
});

// Happy path denial due to ?
export const BHAP4 = scenario("BHAP4", {
  reason: "Child Bonding",
  reason_qualifier: "Adoption",
  residence: "OOS",
  financiallyIneligible: true,
  docs: {
    OOSID: {},
    // @todo: Implement document type.
    PREBIRTH: {
      birthDate: "now -13 months",
    },
  },
});

// Happy path denial due to adoption > 12 months ago.
export const BHAP5 = scenario("BHAP5", {
  reason: "Child Bonding",
  reason_qualifier: "Adoption",
  residence: "OOS",
  docs: {
    OOSID: {},
    // @todo: Implement document type.
    ADOPTIONCERT: {
      adoptionDate: "now -13 months",
    },
  },
});

export const BHAP = chance([
  [1, BHAP1],
  [1, BHAP2],
  [1, BHAP3],
  [1, BHAP4],
  [1, BHAP5],
]);

export default chance([[1, BHAP]]);
