import InputText from "./InputText";
import PropTypes from "prop-types";
import React from "react";

/**
 * Input field allowing users to only enter comma-delimited decimal
 * or whole numbers (determined by the `valueType` prop).
 */
function InputNumber(props) {
  const valueType = props.valueType;
  const inputMode = valueType === "integer" ? "numeric" : "decimal";

  const handleChange = (event) => {
    if (!props.onChange) return;
    const value = event.target.value;
    const allowedCharactersRegex =
      // disallow "." for integers
      valueType === "integer" ? /^-?[\d,]*/g : /^-?[\d.,]*/g;

    // Match against only the characters we want to allow entering,
    // and don't call onChange if the value includes any disallowed characters
    if (value && value.match(allowedCharactersRegex)[0] !== value) {
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

InputNumber.propTypes = {
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
