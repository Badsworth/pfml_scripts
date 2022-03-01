/**
 * Mock of useErrorsLogic
 * Do not use if you need to test side effects of errors
 * state changes
 * @returns {object}
 */
const useErrorsLogic = () => ({
  errors: null,
  setErrors: jest.fn(),
  catchError: jest.fn(),
  clearErrors: jest.fn(),
  clearRequiredFieldErrors: jest.fn(),
});

export default useErrorsLogic;
