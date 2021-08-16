import BaseCollection from "./BaseCollection";
import React from "react";

export default class AppErrorInfoCollection extends BaseCollection {
  // @ts-expect-error ts-migrate(2416) FIXME: Property 'idProperty' in type 'AppErrorInfoCollect... Remove this comment to see the full error message
  get idProperty() {
    return "key";
  }

  /**
   * Get a human readable error message for the given field, if an associated error exists.
   * @param {string} field - field name
   * @returns {?string} Internationalized error message, or `null` if there is no associated error for the field.
   */
  fieldErrorMessage(field) {
    // @ts-expect-error ts-migrate(2339) FIXME: Property 'items' does not exist on type 'AppErrorI... Remove this comment to see the full error message
    if (!this.items.length) return null;

    // @ts-expect-error ts-migrate(2339) FIXME: Property 'items' does not exist on type 'AppErrorI... Remove this comment to see the full error message
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
