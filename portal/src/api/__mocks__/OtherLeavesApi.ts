// Export mocked OtherLeavesApi functions so we can spy on them
// e.g.
// import { removeEmployerBenefit } from "./src/api/OtherLeavesApi";
// expect(removeEmployerBenefit).toHaveBeenCalled();
export const removeEmployerBenefit = jest.fn(
  (applicationId, employerBenefitId) => {
    return Promise.resolve();
  }
);

export const removeOtherIncome = jest.fn((applicationId, otherIncomeId) => {
  return Promise.resolve();
});

export const removePreviousLeave = jest.fn((applicationId, previousLeaveId) => {
  return Promise.resolve();
});

const otherLeavesApi = jest.fn().mockImplementation(() => ({
  removeEmployerBenefit,
  removeOtherIncome,
  removePreviousLeave,
}));

export default otherLeavesApi;
