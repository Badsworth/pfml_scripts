import InputText from "./InputText";
import PropTypes from "prop-types";
import React from "react";

/**
 * Input field allowing users to only enter comma-delimited decimal
 * or whole numbers (determined by the `valueType` prop).
 */
function InputNumber(props) {
  const valueType = props.valueType;
  const allowDecimals = !(valueType === "integer")
  const allowNegative = props.allowNegative;

  const inputMode = valueType === "integer" ? "numeric" : "decimal";

  const handleChange = (event) => {
    if (!props.onChange) return;
    const value = event.target.value;

    // Don't call onChange if the value includes any disallowed characters
    if (value && !isAllowedValue(value, allowDecimals, allowNegative)) {
      event.stopPropagation();
      return;
    }

    props.onChange(event);
  };

  return (
    <InputText
      inputMode={inputMode} // sets a sane default but allows props to override it
      {...props}
      onChange={handleChange}
      type="text"
    />
  );
}

/**
 * Checks if the given value is allowed in this input field.
 * @function isAllowedValue
 * @param {string} value - The user-generated input.
 * @param {boolean} allowDecimals - Controls whether or not numbers with decimals are allowed.
 * @param {boolean} allowNegative - Controls whether or not negative numbers are allowed.
 */
export function isAllowedValue(value, allowDecimals, allowNegative) {
  if (!isNumber(value, allowDecimals)) {
    return false
  }

  if (!allowNegative && isNegative(value)) {
    return false;
  }

  return true;
}

/**
 * Checks if the given value is a number.
 * Allows digits, ie "123"
 * Allows commas, ie "1,234"
 * Allows optional leading hyphens for negative numbers, ie "-123"
 * Optionally allows decimals, ie "1,234.56"
 * @function isNumber
 * @param {string} value - The user-generated input.
 * @param {boolean} allowDecimals - Controls whether or not numbers with decimals are allowed.
 */
function isNumber(value, allowDecimals) {
  // digits, with optional commas, and optional leading hyphen for negatives
  const digits = /^-?[\d,]*/g;

  // digits, with optional commas, decimals, and leading hyphen for negatives
  const digitsWithDecimals = /^-?[\d,.]*/g;

  const allowedCharacters = allowDecimals ? digitsWithDecimals : digits;

  const matches = value.match(allowedCharacters)
  return matches != null && matches[0] === value;
}

/**
 * Checks if the given value is a negative number.
 * @function isNumber
 * @param {string} value - The user-generated input.
 */
function isNegative(value) {
  return value.charAt(0) === "-"
}

InputNumber.propTypes = {
  /**
   * Whether or not to allow negative numbers.
   * If set to true, `onChange` will be skipped if a negative number is input.
   */
  allowNegative: PropTypes.bool,
  /**
   * HTML input `autocomplete` attribute
   */
  autoComplete: PropTypes.string,
  /**
   * Localized error message. Setting this enables the error state styling.
   */
  errorMsg: PropTypes.node,
  /**
   * Localized example text
   */
  example: PropTypes.string,
  /**
   * Additional classes to include on the containing form group element
   */
  formGroupClassName: PropTypes.string,
  /**
   * Localized hint text
   */
  hint: PropTypes.node,
  /**
   * Additional classes to include on the HTML input
   */
  inputClassName: PropTypes.string,
  /**
   * Unique HTML id attribute (created by useUniqueId if null)
   */
  inputId: PropTypes.string,
  /**
   * HTML input `inputmode` attribute. Browsers use this attribute
   * to inform the type of keyboard displayed to the user.
   */
  inputMode: PropTypes.oneOf(["decimal", "numeric", "text"]),
  /**
   * Add a `ref` to the input element
   */
  inputRef: PropTypes.object,
  /**
   * Localized field label
   */
  label: PropTypes.node.isRequired,
  /**
   * Override the label's default text-bold class
   */
  labelClassName: PropTypes.string,
  /**
   * Apply formatting to the field that's unique to the value
   * you expect to be entered. Depending on the mask, the
   * field's appearance and functionality may be affected.
   */
  mask: PropTypes.oneOf(["currency", "hours"]),
  /**
   * Include functionality specific to Personally identifiable information (PII).
   * This will clear initial masked values on focus and reset
   * that value on blur if no change is made
   */
  pii: PropTypes.bool,
  /**
   * HTML input `maxlength` attribute
   */
  maxLength: PropTypes.string,
  /**
   * HTML input `name` attribute
   */
  name: PropTypes.string.isRequired,
  /**
   * HTML input `onBlur` attribute
   */
  onBlur: PropTypes.func,
  /**
   * HTML input `onFocus` attribute
   */
  onFocus: PropTypes.func,
  /**
   * HTML input `onChange` attribute
   */
  onChange: PropTypes.func,
  /**
   * Localized text indicating this field is optional
   */
  optionalText: PropTypes.node,
  /**
   * Enable the smaller label variant
   */
  smallLabel: PropTypes.bool,
  /**
   * Change the width of the input field
   */
  width: PropTypes.oneOf(["small", "medium"]),
  /**
   * Sets the input's `value`. Use this in combination with `onChange`
   * for a controlled component.
   */
  value: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  /**
   * Set the expected value type. This is also used for
   * setting the default inputMode.
   */
  valueType: PropTypes.oneOf(["float", "integer", "string"]),
};

export default InputNumber;
