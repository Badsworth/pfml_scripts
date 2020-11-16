import { DocumentsRequestError, ValidationError } from "../errors";
import AppErrorInfo from "../models/AppErrorInfo";
import AppErrorInfoCollection from "../models/AppErrorInfoCollection";
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
    if (error instanceof ValidationError) {
      handleValidationError(error);
    } else if (error instanceof DocumentsRequestError) {
      handleDocumentsRequestError(error);
    } else {
      console.error(error);
      handleError(error);
    }
  };

  /**
   * Convenience method for setting errors to null
   * @callback clearErrorsFunction
   */
  const clearErrors = () => {
    setAppErrors(() => new AppErrorInfoCollection());
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
  const getMessageFromApiIssue = (
    { field, message, rule, type },
    i18nPrefix
  ) => {
    let fieldOrRuleKey;

    if (field) {
      // Remove array indexes from the field since the array index is not relevant for the error message
      // i.e. convert foo[0].bar[1].cat to foo.bar.cat
      fieldOrRuleKey = `errors.${i18nPrefix}.${field}.${type}`
        .replace(/\[(\d+)\]/g, "")
        // Also convert foo.0.bar.1.cat to foo.bar.cat in case
        .replace(/\.(\d+)/g, "");
    } else if (rule) {
      fieldOrRuleKey = `errors.${i18nPrefix}.rules.${rule}`;
    }

    // 1. Display a field or rule-level message if present:
    //    a. Field-level: "errors.claims.ssn.required" => "Please enter your SSN."
    //    b. Rule-level: "errors.claims.rules.min_leave_periods" => "At least one leave period is required."
    const fieldOrRuleMessage = t(fieldOrRuleKey, { field });

    // When a translation is missing, the key will be returned
    if (fieldOrRuleMessage !== fieldOrRuleKey) {
      return fieldOrRuleMessage;
    }

    tracker.trackEvent("Missing i18n - issue message", {
      i18nKey: fieldOrRuleKey,
    });

    // 3. Display generic message if present: "errors.validationFallback.pattern" => "Field (ssn) is invalid format."
    const fallbackKey = `errors.validationFallback.${type}`;
    const fallbackMessage = t(fallbackKey, { field });
    if (fallbackMessage !== fallbackKey) {
      return fallbackMessage;
    }

    tracker.trackEvent("Missing i18n - issue message", {
      i18nKey: fallbackKey,
    });

    // 4. Display API message if present
    // 5. Otherwise fallback to a generic validation failure message
    return message || t("errors.validationFallback.invalid", { field });
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
   * Add and track the Error
   * @param {DocumentsRequestError} error
   */
  const handleDocumentsRequestError = (error) => {
    const appError = new AppErrorInfo({
      name: error.name,
      message: error.issue
        ? getMessageFromApiIssue(error.issue, "documents")
        : t("errors.caughtError", { context: error.name }),
      meta: {
        application_id: error.application_id,
        file_id: error.file_id,
      },
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
        rule: issue.rule,
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

    // ValidationError can be expected, so to avoid adding noise to the
    // "Errors" section in New Relic, we track these as custom events instead
    tracker.trackEvent(error.name, trackerCustomAttrs);
  };

  return {
    appErrors,
    setAppErrors,
    catchError,
    clearErrors,
  };
};

export default useAppErrorsLogic;
