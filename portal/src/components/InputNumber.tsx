import InputText from "./InputText";
import React from "react";

interface InputNumberProps {
  /**
   * Whether or not to allow negative numbers.
   * If set to true, `onChange` will be skipped if a negative number is input.
   */
  allowNegative?: boolean;
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
   * HTML input `inputmode` attribute. Browsers use this attribute
   * to inform the type of keyboard displayed to the user.
   */
  inputMode?: "decimal" | "numeric" | "text";
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
   * Apply formatting to the field that's unique to the value
   * you expect to be entered. Depending on the mask, the
   * field's appearance and functionality may be affected.
   */
  mask?: "currency" | "hours";
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
  value?: string | number;
  /**
   * Set the expected value type. This is also used for
   * setting the default inputMode.
   */
  valueType?: "float" | "integer" | "string";
}

/**
 * Input field allowing users to only enter comma-delimited decimal
 * or whole numbers (determined by the `valueType` prop).
 */
function InputNumber(props: InputNumberProps) {
  const valueType = props.valueType;
  const allowDecimals = !(valueType === "integer");
  const allowNegative = props.allowNegative;

  const inputMode = valueType === "integer" ? "numeric" : "decimal";

  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
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
 */
export function isAllowedValue(
  value: string,
  allowDecimals: boolean,
  allowNegative?: boolean
) {
  if (!isNumber(value, allowDecimals)) {
    return false;
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
 */
function isNumber(value: string, allowDecimals: boolean) {
  // digits, with optional commas, and optional leading hyphen for negatives
  const digits = /^-?[\d,]*/g;

  // digits, with optional commas, decimals, and leading hyphen for negatives
  const digitsWithDecimals = /^-?[\d,.]*/g;

  const allowedCharacters = allowDecimals ? digitsWithDecimals : digits;

  const matches = value.match(allowedCharacters);
  return matches != null && matches[0] === value;
}

/**
 * Checks if the given value is a negative number.
 */
function isNegative(value: string) {
  return value.charAt(0) === "-";
}

export default InputNumber;
