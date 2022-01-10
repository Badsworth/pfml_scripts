/* eslint-disable no-param-reassign */
import { MockEmployerClaimBuilder } from "./mock-model-builder";

/**
 * Creates mock employer claim
 * @param {Array} types - types of claim to create
 * @returns {EmployerClaim}
 *
 * @example
 * createMockEmployerClaim("continuous", "reducedSchedule")
 */
export const createMockEmployerClaim = (...types) => {
  const isIntermittentLeave = types.includes("intermittent");

  return types
    .reduce((acc, type) => {
      return type === "completed"
        ? (acc = acc[type](isIntermittentLeave))
        : (acc = acc[type]());
    }, new MockEmployerClaimBuilder())
    .create();
};
