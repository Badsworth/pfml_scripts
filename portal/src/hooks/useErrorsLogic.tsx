import {
  AuthSessionMissingError,
  BasePortalError,
  CognitoAuthError,
  ErrorWithIssues,
  InternalServerError,
  ValidationError,
} from "../errors";
import { PortalFlow } from "./usePortalFlow";
import routes from "../routes";
import tracker from "../services/tracker";
import { useState } from "react";

function trackError(error: Error | ErrorWithIssues) {
  if (error instanceof CognitoAuthError) {
    tracker.trackEvent("AuthError", {
      errorCode: error.cognitoError.code,
      errorMessage: error.cognitoError.message,
      errorName: error.cognitoError.name,
    });
  } else if (
    error instanceof BasePortalError &&
    error.issues &&
    error.issues.length > 0
  ) {
    error.issues.forEach(({ field, namespace, rule, type }) => {
      tracker.trackEvent(error.name, {
        // Do not log the error message, since it's not guaranteed that it won't include PII.
        // For example, issues thrown from OpenAPI validation logic sometimes includes the field value.
        issueField: field ?? "",
        issueNamespace: namespace,
        issueRule: rule ?? "",
        issueType: type ?? "",
      });
    });
  } else if (error instanceof BasePortalError) {
    tracker.trackEvent(error.name, {
      errorMessage: error.message,
      errorName: error.name,
    });
  } else {
    // Unexpected error, so track it as a JS exception
    tracker.noticeError(error);
  }
}

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
    } else if (error instanceof Error) {
      handleError(error);
    } else {
      handleError(new InternalServerError());
    }

    // Log non-Portal errors for further debugging support
    if (!(error instanceof BasePortalError)) {
      console.error(error);
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
          error.issues.filter((issue) => issue.type !== "required")
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
    trackError(error);
    portalFlow.goTo(routes.auth.login, { next: portalFlow.pathWithParams });
  };

  /**
   * Add and track the Error
   */
  const handleError = (error: Error | ErrorWithIssues) => {
    addError(error);
    trackError(error);
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
