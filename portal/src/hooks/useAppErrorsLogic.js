import AppErrorInfo from "../models/AppErrorInfo";
import AppErrorInfoCollection from "../models/AppErrorInfoCollection";
import { ValidationError } from "../errors";
import tracker from "../services/tracker";
import useCollectionState from "./useCollectionState";
import { useTranslation } from "../locales/i18n";

/**
 * React hook for creating and managing the state of app errors in an AppErrorInfoCollection
 * @returns {{ appErrors: AppErrorInfoCollection, setAppErrors: Function, catchError: catchErrorFunction, clearErrors: clearErrorsFunction }}
 */
const useAppErrorsLogic = () => {
  const { t } = useTranslation();

  /**
   * State representing both application errors and
   * validation errors
   * @type {{addItem: (error: AppErrorInfo) => undefined, collection: AppErrorInfoCollection, setCollection: Function}}
   */
  const {
    addItem: addError,
    collection: appErrors,
    setCollection: setAppErrors,
  } = useCollectionState(new AppErrorInfoCollection());

  /**
   * Converts a JavaScript error into an AppErrorInfo object and adds it to the app error collection
   * @callback catchErrorFunction
   * @param {Error} error - Error or custom subclass of Error
   */
  const catchError = (error) => {
    console.error(error);

    if (error instanceof ValidationError) {
      handleValidationError(error);
    } else {
      handleError(error);
    }
  };

  /**
   * Convenience method for setting errors to null
   * @callback clearErrorsFunction
   */
  const clearErrors = () => {
    setAppErrors(new AppErrorInfoCollection());
  };

  /**
   * Convert an API error/warning into a user friendly message
   * @param {object} issue - API error/warning
   * @param {string} issue.field
   * @param {string} issue.message - Technical message intended for debugging purposes, but
   *  can be used as a last resort if no other message is available.
   * @param {string} issue.rule
   * @param {string} issue.type
   * @param {string} i18nPrefix - prefix used in the i18n key
   * @returns {string} Internationalized error message
   * @example getMessageFromApiIssue(issue, "claims");
   */
  const getMessageFromApiIssue = ({ field, message, type }, i18nPrefix) => {
    const fallbackMessage = message || "errors.validationFallback.invalid";

    // 1. Field-level message: "errors.claim.ssn.required" => "Please enter your SSN."
    // 2. Generic message: "errors.fallback.pattern" => "Field (ssn) is invalid format."
    // 3. Fallback to API message as last resort
    return t(
      [
        `errors.${i18nPrefix}.${field}.${type}`,
        `errors.validationFallback.${type}`,
        fallbackMessage,
      ],
      {
        field,
      }
    );
  };

  /**
   * Add and track the Error
   * @param {Error} error
   */
  const handleError = (error) => {
    const appError = new AppErrorInfo({
      name: error.name,
      message: t("errors.caughtError", { context: error.name }),
    });

    addError(appError);

    tracker.noticeError(error);
  };

  /**
   * Add and track issues in a ValidationError
   * @param {ValidationError} error
   */
  const handleValidationError = (error) => {
    error.issues.forEach((issue) => {
      const appError = new AppErrorInfo({
        field: issue.field,
        message: getMessageFromApiIssue(issue, error.i18nPrefix),
        name: error.name,
      });

      addError(appError);
    });

    const trackerCustomAttrs = {
      // Reduce issues down to properties we know for a fact shouldn't have PII
      issues: error.issues.map(({ field, rule, type, ...ignored }) => ({
        field,
        rule,
        type,
      })),
    };

    tracker.noticeError(error, trackerCustomAttrs);
  };

  return {
    appErrors,
    setAppErrors,
    catchError,
    clearErrors,
  };
};

export default useAppErrorsLogic;
