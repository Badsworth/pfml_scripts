import {
  ApiRequestError,
  AuthSessionMissingError,
  CognitoAuthError,
  DocumentsLoadError,
  DocumentsUploadError,
  ValidationError,
} from "../errors";
import AppErrorInfo from "../models/AppErrorInfo";
import AppErrorInfoCollection from "../models/AppErrorInfoCollection";
import React from "react";
import { Trans } from "react-i18next";
import routes from "../routes";
import tracker from "../services/tracker";
import useCollectionState from "./useCollectionState";
import { useTranslation } from "../locales/i18n";

/**
 * React hook for creating and managing the state of app errors in an AppErrorInfoCollection
 * @param {object} params
 * @param {object} params.portalFlow
 * @returns {{ appErrors: AppErrorInfoCollection, setAppErrors: Function, catchError: catchErrorFunction, clearErrors: clearErrorsFunction }}
 */
const useAppErrorsLogic = ({ portalFlow }) => {
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
    if (error instanceof AuthSessionMissingError) {
      handleAuthSessionMissingError(error);
    } else if (error instanceof ValidationError) {
      handleValidationError(error);
    } else if (
      error instanceof DocumentsLoadError ||
      error instanceof DocumentsUploadError
    ) {
      handleDocumentsError(error);
    } else if (error instanceof CognitoAuthError) {
      handleCognitoAuthError(error);
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
   * @returns {string | Trans} Internationalized error message or Trans component
   * @example getMessageFromIssue(issue, "claims");
   */
  const getMessageFromIssue = ({ field, message, rule, type }, i18nPrefix) => {
    let issueMessageKey;

    if (field) {
      // Remove array indexes from the field since the array index is not relevant for the error message
      // i.e. convert foo[0].bar[1].cat to foo.bar.cat
      issueMessageKey = `errors.${i18nPrefix}.${field}.${type}`
        .replace(/\[(\d+)\]/g, "")
        // Also convert foo.0.bar.1.cat to foo.bar.cat in case
        .replace(/\.(\d+)/g, "");
    } else if (rule) {
      issueMessageKey = `errors.${i18nPrefix}.rules.${rule}`;
    } else if (type) {
      issueMessageKey = `errors.${i18nPrefix}.${type}`;
    }

    // TODO (CP-1532): Remove once links in error messages are fully supported
    if (type === "fineos_case_creation_issues") {
      return (
        <Trans
          i18nKey={issueMessageKey}
          components={{
            "mass-gov-form-link": (
              <a href="https://www.mass.gov/forms/apply-for-paid-leave-if-you-received-an-error" />
            ),
          }}
        />
      );
    }

    // TODO (CP-1532): Remove once links in error messages are fully supported
    if (type === "intermittent_interval_maximum") {
      return (
        <Trans
          i18nKey={issueMessageKey}
          components={{
            "intermittent-leave-guide": (
              <a href={routes.external.massgov.intermittentLeaveGuide} />
            ),
          }}
        />
      );
    }

    // 1. Display a field or rule-level message if present:
    //    a. Field-level: "errors.claims.ssn.required" => "Please enter your SSN."
    //    b. Rule-level: "errors.claims.rules.min_leave_periods" => "At least one leave period is required."
    const issueMessage = t(issueMessageKey, { field });

    // When a translation is missing, the key will be returned
    if (issueMessage !== issueMessageKey && issueMessage) {
      return issueMessage;
    }

    // 3. Display generic message if present: "errors.validationFallback.pattern" => "Field (ssn) is invalid format."
    const fallbackKey = `errors.validationFallback.${type}`;
    const fallbackMessage = t(fallbackKey, { field });
    if (fallbackMessage !== fallbackKey) {
      return fallbackMessage;
    }

    // 4. Display API message if present
    // 5. Otherwise fallback to a generic validation failure message
    return message || t("errors.validationFallback.invalid", { field });
  };

  /**
   * Handle and track the AuthSessionMissingError
   * @param {AuthSessionMissingError} error
   */
  const handleAuthSessionMissingError = (error) => {
    tracker.trackEvent("AuthSessionMissingError", {
      errorMessage: error.message,
      errorName: error.name,
    });

    portalFlow.goTo(routes.auth.login, { next: portalFlow.pathWithParams });
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

    if (error instanceof ApiRequestError) {
      tracker.trackEvent("ApiRequestError", {
        errorMessage: error.message,
        errorName: error.name,
      });
    } else {
      tracker.noticeError(error);
    }
  };

  /**
   * Add and track documents-related error or issue
   * @param {DocumentsLoadError|DocumentsUploadError} error
   */
  const handleDocumentsError = (error) => {
    const appError = new AppErrorInfo({
      name: error.name,
      message: error.issue
        ? getMessageFromIssue(error.issue, "documents")
        : t("errors.caughtError", { context: error.name }),
      meta: {
        application_id: error.application_id,
        file_id: error.file_id,
      },
    });

    addError(appError);

    tracker.trackEvent(error.name, {
      issueField: error.issue ? error.issue.field : null,
      issueRule: error.issue ? error.issue.rule : null,
      issueType: error.issue ? error.issue.type : null,
    });
  };

  /**
   * Add and track issues in a ValidationError
   * @param {ValidationError} error
   */
  const handleValidationError = (error) => {
    error.issues.forEach((issue) => {
      const appError = new AppErrorInfo({
        field: issue.field,
        message: getMessageFromIssue(issue, error.i18nPrefix),
        name: error.name,
        rule: issue.rule,
        type: issue.type,
      });

      addError(appError);
    });

    // ValidationError can be expected, so to avoid adding noise to the
    // "Errors" section in New Relic, we track these as custom events instead
    error.issues.forEach(({ field, rule, type, ...ignored }) => {
      tracker.trackEvent(error.name, {
        // Do not log the error message, since it's not guaranteed that it won't include PII.
        // For example, issues thrown from OpenAPI validation logic sometimes includes the field value.
        issueField: field,
        issueRule: rule,
        issueType: type,
      });
    });
  };

  /**
   * Add and track issues in a CognitoAuthError
   * @param {CognitoAuthError} error
   */
  const handleCognitoAuthError = (error) => {
    const appError = new AppErrorInfo({
      name: error.name,
      message: error.issue
        ? getMessageFromIssue(error.issue, "auth")
        : t("errors.network"),
    });

    addError(appError);

    tracker.trackEvent("AuthError", {
      errorCode: error.cognitoError.code,
      errorMessage: error.cognitoError.message,
      errorName: error.cognitoError.name,
    });
  };

  return {
    appErrors,
    setAppErrors,
    catchError,
    clearErrors,
  };
};

export default useAppErrorsLogic;
