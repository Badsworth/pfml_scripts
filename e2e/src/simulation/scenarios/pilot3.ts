import { scenario, chance } from "../simulate";

/**
 * This file contains the business simulation for Pilot 3.
 *
 * The overall simulation consists of several groups. Within each group, a number
 * of scenarios are defined. Each time this scenario's generator is invoked, it
 * returns a single scenario, selected by probability.
 *
 * @see chance()
 * @see generate()
 */
// Happy path scenarios.

// Simple claim, MA resident:
const HAP1 = scenario({
  residence: "MA-proofed",
});
// Simple claim, OOS resident.
const HAP2 = scenario({
  residence: "OOS",
});
// Simple denial, MA resident.
const HAP3 = scenario({
  residence: "MA-proofed",
  financiallyIneligible: true,
});

// Combine Happy path scenarios into a single group:
const HAP = chance([
  [1, HAP1],
  [1, HAP2],
  [1, HAP3],
]);

// // Missing HCP, MA Resident
// const GBR1 = scenario("GBR1", {
//   residence: "MA-proofed",
//   financiallyIneligible: true,
//   missingDocs: ["HCP"],
// });
// // Missing HCP, OOS Resident
// const GBR2 = scenario("GBR2", {
//   residence: "OOS",
//   financiallyIneligible: true,
//   missingDocs: ["HCP"],
// });
// // Aggregated "Good but... request" scenarios.
// const GBR = chance("GBR", [
//   [1, GBR1],
//   [1, GBR2],
// ]);
//
// // Mailed HCP, MA Resident
// const GBM1 = scenario("GBM1", {
//   residence: "MA-proofed",
//   financiallyIneligible: true,
//   missingDocs: ["HCP"],
//   mailedDocs: ["HCP"],
// });
// // Mailed HCP, MA Resident
// const GBM2 = scenario("GBM2", {
//   residence: "OOS",
//   financiallyIneligible: true,
//   missingDocs: ["HCP"],
//   mailedDocs: ["HCP"],
// });
// // Aggregated Good but... mail scenarios.
// const GBM = chance("GBM", [
//   [1, GBM1],
//   [1, GBM2],
// ]);
//
// // Aggregated "Good but..." scenarios"
// const GB = chance("GB", [
//   [1, GBR],
//   [1, GBM],
// ]);
//
// // Employer Exempt
// const UNH1 = scenario("UNH1", {
//   residence: "MA-proofed",
//   employerExempt: true,
// });
// // Invalid HCP
// const UNH2 = scenario("UNH2", {
//   residence: "OOS",
//   invalidHCP: true,
// });
// // Mismatched ID/SSN
// const UNH3 = scenario("UNH3", {
//   residence: "MA-unproofed",
// });
// // Short Notice
// const UNH4 = scenario("UNH4", {
//   residence: "MA-proofed",
//   gaveAppropriateNotice: false,
// });
// const UNH = chance("UNH", [
//   [1, UNH1],
//   [1, UNH2],
//   [1, UNH3],
//   [1, UNH4],
// ]);

export default chance([[1, HAP]]);
