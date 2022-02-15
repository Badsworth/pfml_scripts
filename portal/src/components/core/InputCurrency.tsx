import React, { useState } from "react";
import InputNumber from "./InputNumber";
import { maskValue } from "./NumberMask";

interface InputCurrencyProps {
  /**
   * HTML input `autocomplete` attribute
   */
  autoComplete?: string;
  /**
   * Localized error message. Setting this enables the error state styling.
   */
  errorMsg?: React.ReactNode;
  /**
   * Localized example text
   */
  example?: string;
  /**
   * Additional classes to include on the containing form group element
   */
  formGroupClassName?: string;
  /**
   * Localized hint text
   */
  hint?: React.ReactNode;
  /**
   * Additional classes to include on the HTML input
   */
  inputClassName?: string;
  /**
   * Unique HTML id attribute (created by useUniqueId if null)
   */
  inputId?: string;
  /**
   * Add a `ref` to the input element
   */
  inputRef?: React.MutableRefObject<HTMLInputElement>;
  /**
   * Localized field label
   */
  label: React.ReactNode;
  /**
   * Override the label's default text-bold class
   */
  labelClassName?: string;
  /**
   * Include functionality specific to Personally identifiable information (PII).
   * This will clear initial masked values on focus and reset
   * that value on blur if no change is made
   */
  pii?: boolean;
  /**
   * HTML input `maxlength` attribute
   */
  maxLength?: number;
  /**
   * HTML input `name` attribute
   */
  name: string;
  onBlur?: React.FocusEventHandler<HTMLInputElement>;
  onFocus?: React.FocusEventHandler<HTMLInputElement>;
  onChange?: React.ChangeEventHandler<HTMLInputElement>;
  /**
   * Localized text indicating this field is optional
   */
  optionalText?: React.ReactNode;
  /**
   * Enable the smaller label variant
   */
  smallLabel?: boolean;
  /**
   * Change the width of the input field
   */
  width?: "small" | "medium";
  /**
   * Sets the input's `value`. Use this in combination with `onChange`
   * for a controlled component.
   */
  value?: number;
}

const maskCurrency = (value: InputCurrencyProps["value"]) =>
  maskValue(String(value ?? ""), "currency");

/**
 * Input field that displays number values to users as en-us currency
 */
const InputCurrency = (props: InputCurrencyProps) => {
  const [maskedValue, setMaskedValue] = useState(maskCurrency(props.value));

  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const maskedValue = event.target.value;
    // getInputValueFromEvent will strip comma masks from value
    // store masked value to be displayed to user
    setMaskedValue(maskedValue);
    if (props.onChange) {
      props.onChange(event);
    }
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

export default InputCurrency;
