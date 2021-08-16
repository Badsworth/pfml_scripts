// Export mocked OtherLeavesApi functions so we can spy on them
// e.g.
// import { removeEmployerBenefit } from "./src/api/OtherLeavesApi";
// expect(removeEmployerBenefit).toHaveBeenCalled();
// @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
export const removeEmployerBenefit = jest.fn(
  (applicationId, employerBenefitId) => {
    return Promise.resolve();
  }
);

// @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
export const removeOtherIncome = jest.fn((applicationId, otherIncomeId) => {
  return Promise.resolve();
});

// @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
export const removePreviousLeave = jest.fn((applicationId, previousLeaveId) => {
  return Promise.resolve();
});

// @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
const otherLeavesApi = jest.fn().mockImplementation(() => ({
  removeEmployerBenefit,
  removeOtherIncome,
  removePreviousLeave,
}));

export default otherLeavesApi;
