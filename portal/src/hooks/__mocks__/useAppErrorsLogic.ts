/**
 * Mock of useAppErrorsLogic
 * Do not use if you need to test side effects of appErrors
 * state changes
 * @returns {object}
 */
const useAppErrorsLogic = () => ({
  appErrors: null,
  // @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
  setAppErrors: jest.fn(),
  // @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
  catchError: jest.fn(),
  // @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
  clearErrors: jest.fn(),
  // @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
  clearRequiredFieldErrors: jest.fn(),
});

export default useAppErrorsLogic;
