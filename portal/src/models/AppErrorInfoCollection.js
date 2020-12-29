import BaseCollection from "./BaseCollection";
import React from "react";

export default class AppErrorInfoCollection extends BaseCollection {
  get idProperty() {
    return "key";
  }

  /**
   * Get a human readable error message for the given field, if an associated error exists.
   * @param {string} field - field name
   * @returns {?string} Internationalized error message, or `null` if there is no associated error for the field.
   */
  fieldErrorMessage(field) {
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
