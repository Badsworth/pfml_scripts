import { scenario, chance } from "../simulate";
import subMonths from "date-fns/subMonths";
import formatISO from "date-fns/formatISO";

// Cases drawn from: https://massgov.sharepoint.com/:x:/r/sites/EOL-PFMLProject/_layouts/15/Doc.aspx?sourcedoc=%7B7541FAF6-B95A-48F0-B7EA-24CD06E52CF0%7D&file=Cases%20to%20Create%20v1.xlsx&action=default&mobileredirect=true

export const BHAP1 = scenario("BHAP1", {
  reason: "Child Bonding",
  reason_qualifier: "Foster Care",
  residence: "MA-proofed",
  docs: {
    MASSID: {},
    FOSTERPLACEMENT: {},
  },
});

export const BHAP2 = scenario("BHAP2", {
  reason: "Child Bonding",
  reason_qualifier: "Adoption",
  residence: "OOS",
  docs: {
    OOSID: {},
    ADOPTIONCERT: {},
  },
});

export const BHAP3 = scenario("BHAP3", {
  reason: "Child Bonding",
  reason_qualifier: "Newborn",
  residence: "MA-proofed",
  docs: {
    MASSID: {},
    PREBIRTH: {},
  },
});

// Happy path denial due to financial eligibility.
export const BHAP4 = scenario("BHAP4", {
  reason: "Child Bonding",
  reason_qualifier: "Newborn",
  residence: "OOS",
  financiallyIneligible: true,
  child_birth_date: formatISO(subMonths(new Date(), 13)),
  docs: {
    OOSID: {},
    PREBIRTH: {},
  },
});

// Happy path denial due to adoption > 12 months ago.
export const BHAP5 = scenario("BHAP5", {
  reason: "Child Bonding",
  reason_qualifier: "Adoption",
  residence: "OOS",
  child_birth_date: formatISO(subMonths(new Date(), 13)),
  docs: {
    OOSID: {},
    // @todo: Implement document type.
    ADOPTIONCERT: {},
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
