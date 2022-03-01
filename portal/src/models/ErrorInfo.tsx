import React from "react";
import { uniqueId } from "lodash";

/**
 * Provides a consistent interface for creating error messages displayed to the user.
 * @property [field] - Path of the field the error is associated with
 * @property key - Unique key used for React `key` prop (https://reactjs.org/docs/lists-and-keys.html)
 * @property message - Internationalized message displayed to the user (like `Error#message`)
 * @property [name] - Name of the error (like `Error#name`)
 * @property [meta] - Additional error data, like the application_id associated with it
 * @property [rule] - Name of validation issue rule (e.g "min_leave_periods", "conditional", etc)
 * @property [type] - Name of validation issue type (e.g "required", "pattern", "date", etc)
 */
class ErrorInfo {
  key: string = uniqueId("ErrorInfo");
  message?: string | JSX.Element;
  name?: string;
  field?: string;
  meta?: { [key: string]: unknown };
  rule?: string;
  type?: string;

  constructor(attrs: Partial<ErrorInfo>) {
    Object.assign(this, attrs);
  }

  /**
   * Get a human readable error message for the given field, if an associated error exists.
   * @param errors - All errors, including those not associated with the given field
   * @param field - The field to get the error message(s) for
   */
  static fieldErrorMessage(errors: ErrorInfo[], field: string) {
    if (!errors.length) return null;

    const fieldErrors = errors.filter((error) => error.field === field);

    if (!fieldErrors.length) {
      return null;
    }

    // Combine all errors for this field into a single message to be rendered
    return fieldErrors.map((error, i) => (
      <React.Fragment key={error.key}>
        {error.message}
        {i < fieldErrors.length - 1 && " "}
      </React.Fragment>
    ));
  }
}

export default ErrorInfo;
