// Export mocked EmployersApi functions so we can spy on them
export const submitClaimReviewMock = jest.fn((absenceId, patchData) =>
  Promise.resolve({
    success: true,
    status: 200,
  })
);

const employersApi = jest.fn().mockImplementation(() => ({
  submitClaimReview: submitClaimReviewMock,
}));

export default employersApi;
