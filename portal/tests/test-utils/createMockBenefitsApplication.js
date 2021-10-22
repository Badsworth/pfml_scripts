import { MockBenefitsApplicationBuilder } from "./mock-model-builder";

/**
 * Creates mock benefit application
 * @param {Array} types - types of application to create
 * @returns {BenefitsApplication}
 *
 * @example
 * createMockBenefitsApplication("continuous", "reducedSchedule")
 */
export const createMockBenefitsApplication = (...types) => {
  return types
    .reduce(
      (acc, type) => (acc = acc[type]()),
      new MockBenefitsApplicationBuilder()
    )
    .create();
};
