import { scenario, chance } from "../simulate";

// Cases drawn from: https://massgov.sharepoint.com/:x:/r/sites/EOL-PFMLProject/_layouts/15/Doc.aspx?sourcedoc=%7B7541FAF6-B95A-48F0-B7EA-24CD06E52CF0%7D&file=Cases%20to%20Create%20v1.xlsx&action=default&mobileredirect=true

// @todo: Check and clarify distinction betwen prebirth, postbirth, and way post birth.
// Then implement that distinction.

// Happy Path Foster
export const BHAP1 = scenario("BHAP1", {
  reason: "Child Bonding",
  reason_qualifier: "Foster Care",
  residence: "MA-proofed",
  docs: {
    MASSID: {},
    FOSTERPLACEMENT: {},
  },
});

// Happy Path Adoptive
export const BHAP2 = scenario("BHAP2", {
  reason: "Child Bonding",
  reason_qualifier: "Adoption",
  residence: "OOS",
  docs: {
    OOSID: {},
    ADOPTIONCERT: {},
  },
});

// Happy Path Gestational/non-gestational
export const BHAP3 = scenario("BHAP3", {
  reason: "Child Bonding",
  reason_qualifier: "Newborn",
  residence: "MA-proofed",
  bondingDate: "future",
  docs: {
    MASSID: {},
  },
});

// Happy path denial due to financial eligibility.
export const BHAP4 = scenario("BHAP4", {
  reason: "Child Bonding",
  reason_qualifier: "Newborn",
  residence: "OOS",
  financiallyIneligible: true,
  bondingDate: "past",
  docs: {
    OOSID: {},
    BIRTHCERTIFICATE: {},
  },
});

// Happy Path Denial for Failed Certification (> 12 months)
export const BHAP5 = scenario("BHAP5", {
  reason: "Child Bonding",
  reason_qualifier: "Adoption",
  residence: "MA-proofed",
  bondingDate: "far-past",
  docs: {
    MASSID: {},
    ADOPTIONCERT: {},
  },
});

// Happy Path Denial for Plan Availability
// @todo: Implement plan availability?
export const BHAP6 = scenario("BHAP6", {
  reason: "Child Bonding",
  reason_qualifier: "Adoption",
  residence: "MA-proofed",
  bondingDate: "far-past",
  docs: {
    MASSID: {},
    ADOPTIONCERT: {},
  },
});

// Happy Path post-birth Gestational/non-gestational
export const BHAP7 = scenario("BHAP7", {
  reason: "Child Bonding",
  reason_qualifier: "Newborn",
  residence: "MA-proofed",
  bondingDate: "past",
  docs: {
    MASSID: {},
    BIRTHCERTIFICATE: {},
  },
});

export const BHAP = chance([
  [1, BHAP1],
  [1, BHAP2],
  [1, BHAP3],
  [1, BHAP4],
  [1, BHAP5],
  [1, BHAP6],
  [1, BHAP7],
]);

// Missing Foster Documentation
export const BGBM1 = scenario("BGBM1", {
  reason: "Child Bonding",
  reason_qualifier: "Foster Care",
  residence: "MA-proofed",
  docs: {
    MASSID: {},
  },
});

export const BGBM2 = scenario("BGBM2", {
  reason: "Child Bonding",
  reason_qualifier: "Adoption",
  residence: "OOS",
  docs: {
    OOSID: {},
  },
});

export const BGBM3 = scenario("BHAP1", {
  reason: "Child Bonding",
  reason_qualifier: "Foster Care",
  residence: "MA-proofed",
  docs: {
    FOSTERPLACEMENT: {},
  },
});

export const BGBM = chance([
  [1, BGBM1],
  [1, BGBM2],
]);

// Birth Document Mismatch
export const BUNH1 = scenario("BUNH1", {
  reason: "Child Bonding",
  reason_qualifier: "Newborn",
  residence: "OOS",
  bondingDate: "past",
  docs: {
    OOSID: {},
    BIRTHCERTIFICATE: {
      invalid: true,
    },
  },
});

// Invalid birth document
export const BUNH2 = scenario("BUNH2", {
  reason: "Child Bonding",
  reason_qualifier: "Newborn",
  residence: "MA-proofed",
  bondingDate: "past",
  docs: {
    MASSID: {},
    PERSONALLETTER: {},
  },
});

// Invalid Cat Documentation
export const BUNH3 = scenario("BUNH3", {
  reason: "Child Bonding",
  reason_qualifier: "Newborn",
  residence: "OOS",
  bondingDate: "past",
  docs: {
    OOSID: {},
    CATPIC: {},
  },
});

// Birth Certificate does not match template
// export const BUNH4 = scenario("BUNH4", {
//   reason: "Child Bonding",
//   reason_qualifier: "Newborn",
//   residence: "MA-proofed",
//   docs: {
//     MASSID: {},
//     // @todo: Implement birth cert that doesn't match template. Question out in spreadsheet to see how this should be
//     //  implemented.
//     // BIRTHCERTIFICATE: {},
//   },
// });

// @todo: Spot check and review documents for each claim type.
// @todo: Spot check that scenarios match spreadsheet.
// @todo: Attempt submission of each scenario type.

export const BUNH = chance([
  [1, BUNH1],
  [1, BUNH2],
  [1, BUNH3],
  // [1, BUNH4],
]);

export default chance([
  [13, BHAP],
  [3, BGBM],
  [4, BUNH],
]);
