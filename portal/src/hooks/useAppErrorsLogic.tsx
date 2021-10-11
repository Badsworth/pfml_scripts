import {
  ApiRequestError,
  AuthSessionMissingError,
  ClaimWithdrawnError,
  CognitoAuthError,
  DocumentsLoadError,
  DocumentsUploadError,
  LeaveAdminForbiddenError,
  NetworkError,
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
  const { i18n, t } = useTranslation();

  /**
   * @callback addErrorFunction
   * @param {AppErrorInfo} error
   */

  /**
   * State representing both application errors and
   * validation errors
   * @type {{addItem: addErrorFunction, collection: AppErrorInfoCollection, setCollection: Function}}
   */
  const {
    addItem: addError,
    collection: appErrors,
    setCollection: setAppErrors,
    // @ts-expect-error ts-migrate(2554) FIXME: Expected 1 arguments, but got 0.
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
    } else if (error instanceof LeaveAdminForbiddenError) {
      handleLeaveAdminForbiddenError(error);
    } else if (error instanceof ClaimWithdrawnError) {
      handleClaimWithdrawnError(error);
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
    // @ts-expect-error ts-migrate(2554) FIXME: Expected 1 arguments, but got 0.
    setAppErrors(() => new AppErrorInfoCollection());
  };

  /**
   * Convenience method for removing required field errors. This is used by the review page
   * to hide required field errors and instead display a more user-friendly message to users
   * that they need to go back and complete all required fields
   * @callback clearErrorsFunction
   */
  const clearRequiredFieldErrors = () => {
    const remainingErrors = appErrors.items.filter(
      (error) => error.type !== "required"
    );

    setAppErrors(() => new AppErrorInfoCollection(remainingErrors));
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
   * @param {Object} [tOptions] - additional key/value pairs used in the i18n message interpolation
   * @returns {string | Trans} Internationalized error message or Trans component
   * @example getMessageFromIssue(issue, "applications");
   */
  const getMessageFromIssue = (
    { field, message, rule, type },
    i18nPrefix,
    tOptions
  ) => {
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

    const htmlErrorMessage = maybeGetHtmlErrorMessage(
      type,
      issueMessageKey,
      tOptions
    );
    if (htmlErrorMessage) return htmlErrorMessage;

    // 1. Display a field or rule-level message if present:
    //    a. Field-level: "errors.applications.ssn.required" => "Please enter your SSN."
    //    b. Rule-level: "errors.applications.rules.min_leave_periods" => "At least one leave period is required."
    const issueMessage = t(issueMessageKey, { field });

    // When a translation is missing, the key will be returned
    if (issueMessage !== issueMessageKey && issueMessage) {
      return issueMessage;
    }

    // 3. Display generic message if present: "errors.validationFallback.pattern" => "Field (ssn) is invalid format."
    if (type) {
      const fallbackKey = `errors.validationFallback.${type}`;
      const fallbackMessage = t(fallbackKey, { field });
      if (fallbackMessage !== fallbackKey) {
        return fallbackMessage;
      }
    }

    // 4. Display API message if present
    // 5. Otherwise fallback to a generic validation failure message
    return message || t("errors.validationFallback.invalid", { field });
  };

  /**
   * Create the custom HTML error message, if the given error type requires HTML formatting/links
   * @param {string} type
   * @param {string} issueMessageKey
   * @param {Object} [tOptions] - additional key/value pairs used in the i18n message interpolation
   * @returns {Trans} React node for the message, if the given error type should have an HTML message
   */
  const maybeGetHtmlErrorMessage = (type, issueMessageKey, tOptions) => {
    if (!issueMessageKey || !i18n.exists(issueMessageKey)) return;

    // TODO (CP-1532): Remove once links in error messages are fully supported
    if (type === "fineos_case_creation_issues") {
      return (
        <Trans
          i18nKey={issueMessageKey}
          components={{
            "mass-gov-form-link": (
              <a
                target="_blank"
                rel="noreferrer noopener"
                href={routes.external.massgov.caseCreationErrorGuide}
              />
            ),
          }}
        />
      );
    }

    if (type === "contains_v1_and_v2_eforms") {
      return (
        <Trans
          i18nKey={issueMessageKey}
          components={{
            "contact-center-phone-link": (
              <a href={`tel:${t("shared.contactCenterPhoneNumber")}`} />
            ),
            /* The h3 header has content defined in en-US.js. */
            /* eslint-disable jsx-a11y/heading-has-content */
            h3: <h3 />,
            ul: <ul />,
            li: <li />,
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
              <a
                target="_blank"
                rel="noreferrer noopener"
                href={routes.external.massgov.intermittentLeaveGuide}
              />
            ),
          }}
        />
      );
    }

    // TODO (CP-1532): Remove once links in error messages are fully supported
    if (type === "unauthorized_leave_admin") {
      return (
        <Trans
          i18nKey={issueMessageKey}
          components={{
            "add-org-link": <a href={routes.employers.addOrganization} />,
          }}
        />
      );
    }

    if (type === "employer_verification_data_required") {
      return (
        <Trans
          i18nKey={issueMessageKey}
          components={{
            "file-a-return-link": (
              <a
                target="_blank"
                rel="noreferrer noopener"
                href={routes.external.massgov.zeroBalanceEmployer}
              />
            ),
          }}
        />
      );
    }

    if (type === "fineos_claim_withdrawn") {
      return (
        <Trans
          i18nKey={issueMessageKey}
          tOptions={tOptions}
          components={{
            "contact-center-phone-link": (
              <a href={`tel:${t("shared.contactCenterPhoneNumber")}`} />
            ),
          }}
        />
      );
    }
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

    // Error may include the response data (potentially PII)
    // we should avoid tracking the entire error in New Relic
    if (error instanceof ApiRequestError) {
      tracker.trackEvent("ApiRequestError", {
        errorMessage: error.message,
        errorName: error.name,
      });
    } else if (error instanceof NetworkError) {
      tracker.trackEvent("NetworkError", {
        errorMessage: error.message,
        errorName: error.name,
      });
    } else {
      // @ts-expect-error ts-migrate(2554) FIXME: Expected 2 arguments, but got 1.
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
        ? // @ts-expect-error ts-migrate(2554) FIXME: Expected 3 arguments, but got 2.
          getMessageFromIssue(error.issue, "documents")
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
   * Add and track claim detail withdrawn error
   * @param {ClaimWithdrawnError} error
   */
  const handleClaimWithdrawnError = (error) => {
    const appError = new AppErrorInfo({
      name: error.name,
      message: getMessageFromIssue(error.issue, "claimStatus", {
        absenceId: error.fineos_absence_id,
      }),
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
        // @ts-expect-error ts-migrate(2554) FIXME: Expected 3 arguments, but got 2.
        message: getMessageFromIssue(issue, error.i18nPrefix),
        name: error.name,
        rule: issue.rule,
        type: issue.type,
      });

      addError(appError);
    });

    // ValidationError can be expected, so to avoid adding noise to the
    // "Errors" section in New Relic, we track these as custom events instead
    error.issues.forEach(({ field, rule, type, ..._ignored }) => {
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
        ? // @ts-expect-error ts-migrate(2554) FIXME: Expected 3 arguments, but got 2.
          getMessageFromIssue(error.issue, "auth")
        : t("errors.network"),
    });

    addError(appError);

    tracker.trackEvent("AuthError", {
      errorCode: error.cognitoError.code,
      errorMessage: error.cognitoError.message,
      errorName: error.cognitoError.name,
    });
  };

  /**
   * Redirect to either the Verify Contributions or Cannot Verify page
   * based on if the UserLeaveAdministrator is verifiable.
   * @param {LeaveAdminForbiddenError} error
   */
  const handleLeaveAdminForbiddenError = (error) => {
    tracker.trackEvent("LeaveAdminForbiddenError", {
      errorMessage: error.message,
      errorName: error.name,
      employerId: error.employer_id,
      hasVerificationData: error.has_verification_data,
    });

    if (error.has_verification_data) {
      portalFlow.goTo(routes.employers.verifyContributions, {
        employer_id: error.employer_id,
        next: portalFlow.pathWithParams,
      });
    } else {
      portalFlow.goTo(routes.employers.cannotVerify, {
        employer_id: error.employer_id,
      });
    }
  };

  return {
    appErrors,
    setAppErrors,
    catchError,
    clearErrors,
    clearRequiredFieldErrors,
  };
};

export default useAppErrorsLogic;
