/**
 * Get a form field's value, making appropriate type conversions as necessary.
 *
 * @see https://github.com/navahq/archive-vermont-customer-portal-apps/blob/27b66dd7bf37671a6e33a8d2c51a82c7bd9daa41/online-application-app/src/client/actions/index.js#L150
 * @param {object} event
 * @param {HTMLElement|object} event.target
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

  const { checked, pattern, type, value } = event.target;

  const inputMode =
    // Some components, like InputDate, hijack the change event and pass in a plain object
    // TODO (CP-1667): This condition shouldn't be required once our components stop
    // hijacking event.target
    typeof event.target.getAttribute === "function"
      ? // Use getAttribute for this since some browsers, including Firefox,
        // don't support accessing the value via event.target.inputMode.
        // https://caniuse.com/mdn-api_htmlelement_inputmode
        event.target.getAttribute("inputmode")
      : null;

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
    inputMode === "numeric" &&
    pattern === "[0-9]*" &&
    value &&
    value.trim() !== ""
  ) {
    if (!isNaN(value)) {
      result = Number(value);
    }
  } else if (typeof value === "string" && value.trim() === "") {
    // An empty or empty-looking string will be interpreted as valid
    // in our application_rules, even if it's required. We want to
    // store an empty string as null in order for a required field
    // to fail validation if its value is empty.
    result = null;
  }

  return result;
}
