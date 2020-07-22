/**
 * Get a form field's value, making appropriate type conversions as necessary.
 *
 * @see https://github.com/navahq/archive-vermont-customer-portal-apps/blob/27b66dd7bf37671a6e33a8d2c51a82c7bd9daa41/online-application-app/src/client/actions/index.js#L150
 * @param {object} event
 * @param {object} event.target
 * @param {boolean} [event.target.checked] - if input was radio/checkbox, was it selected?
 * @param {string} event.target.name - The name representing this field in our state
 * @param {*} event.target.value
 * @param {string} [event.target.type] - what type of input is this value coming from (i.e text, radio)
 * @returns {string|boolean}
 */
export default function getInputValueFromEvent(event) {
  if (!event || !event.target) {
    return undefined;
  }

  const { checked, type, value, inputmode, pattern } = event.target;
  let result = value;
  if (type === "checkbox" || type === "radio") {
    // Convert boolean input string values into an actual boolean
    switch (value) {
      case "true":
        result = checked;
        break;
      case "false":
        result = !checked;
        break;
    }
  } else if (
    inputmode === "numeric" &&
    pattern === "[0-9]*" &&
    value &&
    value.trim() !== ""
  ) {
    if (!isNaN(value)) {
      result = Number(value);
    }
  } else if (typeof value === "string" && value.trim() === "") {
    // An empty or empty-looking string will be interpreted as valid
    // in the eyes of JSON Schema, even if marked as "required." So,
    // we want to store an empty string as `undefined` in order for a
    // required field to fail validation if its value is empty.
    result = undefined;
  }

  return result;
}
