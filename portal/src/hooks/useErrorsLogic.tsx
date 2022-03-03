import {
  ApiRequestError,
  AuthSessionMissingError,
  ClaimWithdrawnError,
  CognitoAuthError,
  DocumentsLoadError,
  DocumentsUploadError,
  InternalServerError,
  LeaveAdminForbiddenError,
  NetworkError,
  ValidationError,
} from "../errors";
import { PortalFlow } from "./usePortalFlow";
import { get } from "lodash";
import routes from "../routes";
import tracker from "../services/tracker";
import { useState } from "react";

/**
 * React hook for creating and managing the state of app errors
 */
const useErrorsLogic = ({ portalFlow }: { portalFlow: PortalFlow }) => {
  /**
   * State representing both application errors and
   * validation errors
   */
  const [errors, setErrors] = useState<Error[]>([]);
  const addError = (error: Error) => {
    setErrors((prevErrors) => [...prevErrors, error]);
  };

  /**
   * Store and track the JS error. UI components then manage how the error gets displayed.
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
    } else if (error instanceof Error) {
      console.error(error);
      handleError(error);
    } else {
      console.error(error);
      handleError(new InternalServerError());
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
    const updatedErrors = errors.map((error) => {
      if (error instanceof ValidationError) {
        return new ValidationError(
          error.issues.filter((issue) => issue.type !== "required"),
          error.i18nPrefix
        );
      }

      return error;
    });

    setErrors(updatedErrors);
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
  const handleError = (error: Error) => {
    addError(error);

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

    addError(error);

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

    addError(error);

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
    addError(error);

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
    addError(error);

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
