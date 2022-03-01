import {
  ApiRequestError,
  AuthSessionMissingError,
  ClaimWithdrawnError,
  CognitoAuthError,
  DocumentsLoadError,
  DocumentsUploadError,
  Issue,
  LeaveAdminForbiddenError,
  NetworkError,
  ValidationError,
} from "../errors";
import React, { useState } from "react";
import ErrorInfo from "../models/ErrorInfo";
import { PortalFlow } from "./usePortalFlow";
import { Trans } from "react-i18next";
import { get } from "lodash";
import routes from "../routes";
import tracker from "../services/tracker";
import { useTranslation } from "../locales/i18n";

/**
 * React hook for creating and managing the state of app errors
 */
const useErrorsLogic = ({ portalFlow }: { portalFlow: PortalFlow }) => {
  const { i18n, t } = useTranslation();

  /**
   * State representing both application errors and
   * validation errors
   */
  const [errors, setErrors] = useState<ErrorInfo[]>([]);
  const addError = (error: ErrorInfo) => {
    setErrors((prevErrors) => [...prevErrors, error]);
  };

  /**
   * Converts a JavaScript error into an ErrorInfo object and adds it to the app error collection
   */
  const catchError = (error: unknown) => {
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
   */
  const clearErrors = () => {
    setErrors([]);
  };

  /**
   * Convenience method for removing required field errors. This is used by the review page
   * to hide required field errors and instead display a more user-friendly message to users
   * that they need to go back and complete all required fields
   */
  const clearRequiredFieldErrors = () => {
    const remainingErrors = errors.filter((error) => error.type !== "required");

    setErrors(remainingErrors);
  };

  /**
   * Convert an API error/warning into a user friendly message
   * @param i18nPrefix - prefix used in the i18n key
   * @param [tOptions] - additional key/value pairs used in the i18n message interpolation
   * @example getMessageFromIssue(issue, "applications");
   */
  const getMessageFromIssue = (
    issue: Issue,
    i18nPrefix: string,
    tOptions?: { [key: string]: unknown }
  ) => {
    const { field, message, rule, type } = issue;
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
    if (issueMessageKey && i18n.exists(issueMessageKey)) {
      return t(issueMessageKey, { field });
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
   * @param [tOptions] - additional key/value pairs used in the i18n message interpolation
   */
  const maybeGetHtmlErrorMessage = (
    type?: string,
    issueMessageKey?: string,
    tOptions?: { [key: string]: unknown }
  ) => {
    if (!type || !issueMessageKey || !i18n.exists(issueMessageKey)) return;

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
   */
  const handleAuthSessionMissingError = (error: AuthSessionMissingError) => {
    tracker.trackEvent("AuthSessionMissingError", {
      errorMessage: error.message,
      errorName: error.name,
    });

    portalFlow.goTo(routes.auth.login, { next: portalFlow.pathWithParams });
  };

  /**
   * Add and track the Error
   */
  const handleError = (error: unknown) => {
    const errorName = error instanceof Error ? error.name : "";

    const errorInfo = new ErrorInfo({
      name: errorName,
      message: t("errors.caughtError", { context: errorName }),
    });

    addError(errorInfo);

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
      tracker.noticeError(error);
    }
  };

  /**
   * Add and track documents-related error or issue
   */
  const handleDocumentsError = (
    error: DocumentsLoadError | DocumentsUploadError
  ) => {
    const issue =
      error instanceof DocumentsUploadError ? error.issues[0] : undefined;

    const errorInfo = new ErrorInfo({
      name: error.name,
      message: issue
        ? getMessageFromIssue(issue, "documents")
        : t("errors.caughtError", { context: error.name }),
      meta: {
        application_id: error.application_id,
        file_id:
          error instanceof DocumentsUploadError ? error.file_id : undefined,
      },
    });

    addError(errorInfo);

    tracker.trackEvent(error.name, {
      issueField: get(issue, "field", ""),
      issueRule: get(issue, "rule", ""),
      issueType: get(issue, "type", ""),
    });
  };

  /**
   * Add and track claim detail withdrawn error
   */
  const handleClaimWithdrawnError = (error: ClaimWithdrawnError) => {
    const issue = error.issues[0];
    const errorInfo = new ErrorInfo({
      name: error.name,
      message: getMessageFromIssue(issue, "claimStatus", {
        absenceId: error.fineos_absence_id,
      }),
    });

    addError(errorInfo);

    tracker.trackEvent(error.name, {
      issueField: get(issue, "field", ""),
      issueRule: get(issue, "rule", ""),
      issueType: get(issue, "type", ""),
    });
  };

  /**
   * Add and track issues in a ValidationError
   */
  const handleValidationError = (error: ValidationError) => {
    error.issues.forEach((issue) => {
      const errorInfo = new ErrorInfo({
        field: issue.field,
        message: getMessageFromIssue(issue, error.i18nPrefix),
        name: error.name,
        rule: issue.rule,
        type: issue.type,
      });

      addError(errorInfo);
    });

    // ValidationError can be expected, so to avoid adding noise to the
    // "Errors" section in New Relic, we track these as custom events instead
    error.issues.forEach(({ field, rule, type, ..._ignored }) => {
      tracker.trackEvent(error.name, {
        // Do not log the error message, since it's not guaranteed that it won't include PII.
        // For example, issues thrown from OpenAPI validation logic sometimes includes the field value.
        issueField: field || "",
        issueRule: rule || "",
        issueType: type || "",
      });
    });
  };

  /**
   * Add and track issues in a CognitoAuthError
   */
  const handleCognitoAuthError = (error: CognitoAuthError) => {
    const issue = error.issues[0];

    const errorInfo = new ErrorInfo({
      field: issue?.field,
      name: error.name,
      message:
        typeof issue === "undefined"
          ? t("errors.network")
          : getMessageFromIssue(issue, "auth"),
    });

    addError(errorInfo);

    tracker.trackEvent("AuthError", {
      errorCode: error.cognitoError.code,
      errorMessage: error.cognitoError.message,
      errorName: error.cognitoError.name,
    });
  };

  /**
   * Redirect to either the Verify Contributions or Cannot Verify page
   * based on if the UserLeaveAdministrator is verifiable.
   */
  const handleLeaveAdminForbiddenError = (error: LeaveAdminForbiddenError) => {
    tracker.trackEvent("LeaveAdminForbiddenError", {
      errorMessage: error.message,
      errorName: error.name,
      employerId: error.employer_id,
      hasVerificationData: error.has_verification_data.toString(),
    });

    if (error.has_verification_data) {
      portalFlow.goTo(
        routes.employers.verifyContributions,
        {
          employer_id: error.employer_id,
          next: portalFlow.pathWithParams,
        },
        { redirect: true }
      );
    } else {
      portalFlow.goTo(
        routes.employers.cannotVerify,
        {
          employer_id: error.employer_id,
        },
        { redirect: true }
      );
    }
  };

  return {
    errors,
    setErrors,
    catchError,
    clearErrors,
    clearRequiredFieldErrors,
  };
};

export default useErrorsLogic;
export type ErrorsLogic = ReturnType<typeof useErrorsLogic>;
