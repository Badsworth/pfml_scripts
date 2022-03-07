import { ErrorWithIssues } from "../errors";
import IssueErrorMessage from "../components/IssueErrorMessage";
import React from "react";

/**
 * Renders its internationalized message, if a relevant field-level error exists.
 * This is a function, rather than a React component so that we can return `undefined`.
 * This `undefined` return value then means components can easily exclude error props
 * (like styling) when an error message isn't present.
 */
function findErrorMessageForField(
  errors: ErrorWithIssues[],
  fieldName: string
): JSX.Element | undefined {
  let errorMessage: JSX.Element | undefined;

  errors.some((error) => {
    if (typeof error.issues !== "undefined") {
      const issue = error.issues.find((issue) => issue.field === fieldName);

      if (issue) {
        errorMessage = <IssueErrorMessage {...issue} />;
        return true;
      }
    }

    return false;
  });

  return errorMessage;
}

export default findErrorMessageForField;
