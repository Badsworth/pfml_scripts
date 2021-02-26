import { scenario, chance } from "../simulate";

export const INELIGIBLE = scenario("INELIGIBLE", {
  reason: "Serious Health Condition - Employee",
  residence: "MA-proofed",
  wages: "ineligible",
  docs: {},
});

export const ELIGIBLE30 = scenario("ELIGIBLE30", {
  reason: "Serious Health Condition - Employee",
  residence: "MA-proofed",
  docs: {},
  wages: 30000,
});

export const ELIGIBLE60 = scenario("ELIGIBLE60", {
  reason: "Serious Health Condition - Employee",
  residence: "MA-proofed",
  docs: {},
  wages: 60000,
});

export const ELIGIBLE90 = scenario("ELIGIBLE90", {
  reason: "Serious Health Condition - Employee",
  residence: "MA-proofed",
  docs: {},
  wages: 90000,
});

export default chance([
  [1, INELIGIBLE],
  [1, ELIGIBLE30],
  [1, ELIGIBLE60],
  [1, ELIGIBLE90],
]);
