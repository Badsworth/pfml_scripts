import React, { useState } from "react";
import InputNumber from "./InputNumber";
import PropTypes from "prop-types";
import { maskValue } from "./Mask";

const maskCurrency = (value) => maskValue(String(value || ""), "currency");

/**
 * Input field that displays number values to users as en-us currency
 */
const InputCurrency = (props) => {
  const [maskedValue, setMaskedValue] = useState(maskCurrency(props.value));

  const handleChange = (event) => {
    const maskedValue = event.target.value;
    // getInputValueFromEvent will strip comma masks from value
    // store masked value to be displayed to user
    setMaskedValue(maskedValue);
    props.onChange(event);
  };

  return (
    <InputNumber
      {...props}
      value={maskedValue || maskCurrency(props.value)}
      valueType="float"
      allowNegative
      mask="currency"
      onChange={handleChange}
    />
  );
};

InputCurrency.propTypes = {
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
  value: PropTypes.number,
};

export default InputCurrency;
