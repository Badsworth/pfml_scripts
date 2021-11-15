import AppErrorInfo from "./AppErrorInfo";
import BaseCollection from "./BaseCollection";
import React from "react";

export default class AppErrorInfoCollection extends BaseCollection<AppErrorInfo> {
  get idProperty() {
    return "key";
  }

  /**
   * Get a human readable error message for the given field, if an associated error exists.
   */
  fieldErrorMessage(field: string) {
    if (!this.items.length) return null;

    const fieldErrors = this.items.filter((error) => error.field === field);

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
