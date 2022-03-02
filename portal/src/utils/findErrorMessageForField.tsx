import IssueErrorMessage from "../components/IssueErrorMessage";
import React from "react";
import { TranslatableError } from "../errors";

/**
 * Renders its internationalized message, if a relevant field-level error exists.
 * This is a function, rather than a React component so that we can return `undefined`.
 * This `undefined` return value then means components can easily exclude error props
 * (like styling) when an error message isn't present.
 */
function findErrorMessageForField(
  errors: TranslatableError[],
  fieldName: string
): JSX.Element | undefined {
  let errorMessage: JSX.Element | undefined;

  errors.some((error) => {
    if (
      typeof error.issues !== "undefined" &&
      typeof error.i18nPrefix !== "undefined"
    ) {
      const issue = error.issues.find((issue) => issue.field === fieldName);

      if (issue) {
        errorMessage = (
          <IssueErrorMessage i18nPrefix={error.i18nPrefix} {...issue} />
        );
        return true;
      }
    }

    return false;
  });

  return errorMessage;
}

export default findErrorMessageForField;
