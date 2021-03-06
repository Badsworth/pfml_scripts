/**
 * Get a form field's value, making appropriate type conversions as necessary.
 *
 * @see https://github.com/navahq/archive-vermont-customer-portal-apps/blob/27b66dd7bf37671a6e33a8d2c51a82c7bd9daa41/online-application-app/src/client/actions/index.js#L150
 */
export default function getInputValueFromEvent(
  event?:
    | React.ChangeEvent<
        HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement
      >
    | { [key: string]: undefined }
) {
  if (!event || !event.target) {
    return undefined;
  }

  const { type, value } = event.target;
  const valueType = event.target.getAttribute("data-value-type");

  let result: number | string | boolean | null = value;
  if (
    event.target instanceof HTMLInputElement &&
    (type === "checkbox" || type === "radio")
  ) {
    const checked = event.target.checked;
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
    (valueType === "integer" || valueType === "float") &&
    value &&
    value.trim() !== ""
  ) {
    // Support comma-delimited numbers
    const transformedValue = value.replace(/,/g, "");

    if (
      isNaN(Number(transformedValue)) ||
      // Don't prevent a trailing decimal point, otherwise a user can't enter a decimal number
      (valueType === "float" && transformedValue.endsWith("."))
    )
      return result;

    result =
      valueType === "integer"
        ? parseInt(transformedValue)
        : Number(transformedValue);
  } else if (typeof value === "string" && value.trim() === "") {
    // An empty or empty-looking string will be interpreted as valid
    // in our application_rules, even if it's required. We want to
    // store an empty string as null in order for a required field
    // to fail validation if its value is empty.
    result = null;
  }

  return result;
}
