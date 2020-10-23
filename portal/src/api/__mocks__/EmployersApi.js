import Claim from "../../models/Claim";

// Export mocked EmployersApi functions so we can spy on them

export const getClaimMock = jest.fn().mockResolvedValue((absenceId) => {
  return {
    claim: new Claim({
      fineos_absence_id: absenceId,
    }),
    status: 200,
    success: true,
  };
});

export const submitClaimReviewMock = jest
  .fn()
  .mockResolvedValue((absenceId, patchData) => {
    return {
      claim: null,
      status: 200,
      success: true,
    };
  });

const employersApi = jest.fn().mockImplementation(() => ({
  getClaim: getClaimMock,
  submitClaimReview: submitClaimReviewMock,
}));

export default employersApi;
