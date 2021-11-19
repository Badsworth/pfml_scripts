/**
 * Mock of useAppErrorsLogic
 * Do not use if you need to test side effects of appErrors
 * state changes
 * @returns {object}
 */
const useAppErrorsLogic = () => ({
  appErrors: null,
  setAppErrors: jest.fn(),
  catchError: jest.fn(),
  clearErrors: jest.fn(),
  clearRequiredFieldErrors: jest.fn(),
});

export default useAppErrorsLogic;
