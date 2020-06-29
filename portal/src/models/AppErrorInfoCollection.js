import BaseCollection from "./BaseCollection";

export default class AppErrorInfoCollection extends BaseCollection {
  get idProperty() {
    return "key";
  }

  /**
   * Get a human readable error message for the given field, if an associated error exists.
   * @param {string} field - field name
   * @returns {string} Internationalized error message
   */
  fieldErrorMessage(field) {
    if (!this.items.length) return;

    const fieldErrors = this.items.filter((error) => error.field === field);

    if (!fieldErrors.length) return;

    // Combine all errors for this field into a single message to be rendered
    return fieldErrors.map((error) => error.message).join(" ");
  }
}
