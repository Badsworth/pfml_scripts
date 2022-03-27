import FormLabel from "./FormLabel";
import NumberMask from "./NumberMask";
import React from "react";
import classnames from "classnames";
import isBlank from "../../utils/isBlank";
import usePiiHandlers from "../../hooks/usePiiHandlers";
import useUniqueId from "../../hooks/useUniqueId";

export interface InputTextProps {
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
   * HTML input `inputmode` attribute. Defaults to "text". Browsers
   * use this attribute to inform the type of keyboard displayed
   * to the user.
   */
  inputMode?: "decimal" | "numeric" | "text";
  /**
   * Add a `ref` to the input element
   */
  inputRef?: React.MutableRefObject<HTMLInputElement | null>;
  /**
   * Localized field label
   */
  label: React.ReactNode;
  /**
   * Override the label's default text-bold class
   */
  labelClassName?: string;
  /**
   * Apply formatting to a number-only field. Depending on the mask, the
   * field's appearance and functionality may be affected.
   */
  mask?: "currency" | "fein" | "hours" | "phone" | "ssn" | "zip";
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
   * HTML input `type` attribute. Defaults to "text".
   * Usage of type="number" is not allowed, see:
   * https://css-tricks.com/you-probably-dont-need-input-typenumber/
   */
  type?: "email" | "password" | "tel" | "text";
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
   * Adds a data attribute to the input. Can be used by
   * change handlers or `getInputValueFromEvent` to inform
   * what value type the field should be converted to before
   * saving it back to the API.
   */
  valueType?: "integer" | "float" | "string";
  /**
   * Disable pasting for a field (only should be used on payment method page)
   */
  disablePaste?: boolean;
}

/**
 * Text [input](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/input) field. Also renders
 * supporting UI elements like label, hint text, and error message.
 *
 * [USWDS Reference ↗](https://designsystem.digital.gov/components/form-controls)
 * Masked field functionality copied from [CMS design system](https://design.cms.gov/components/masked-field)
 */
function InputText({ type = "text", ...props }: InputTextProps) {
  let inputId = useUniqueId("InputText");
  inputId = props.inputId || inputId;

  const hasError = !isBlank(props.errorMsg);

  const fieldClasses = classnames("usa-input", props.inputClassName, {
    "usa-input--error": hasError,
    "maxw-mobile-lg": !props.width,
    [`usa-input--${props.width}`]: !!props.width,
  });
  const formGroupClasses = classnames(
    "usa-form-group",
    props.formGroupClassName,
    {
      "usa-form-group--error": hasError,
    }
  );

  const { handleFocus, handleBlur } = usePiiHandlers({
    name: props.name,
    value: props.value,
    onChange: props.onChange,
    onBlur: props.onBlur,
    onFocus: props.onFocus,
  });

  const handleDisablePaste = (e: React.ClipboardEvent<HTMLInputElement>) => {
    e.preventDefault();
    return false;
  };

  const field = (
    <input
      autoComplete={props.autoComplete}
      aria-labelledby={`${inputId}_label ${inputId}_hint ${inputId}_error`}
      className={fieldClasses}
      data-value-type={props.valueType}
      id={inputId}
      inputMode={props.inputMode}
      maxLength={props.maxLength}
      name={props.name}
      onBlur={props.pii ? handleBlur : props.onBlur}
      onFocus={props.pii ? handleFocus : props.onFocus}
      onChange={props.onChange}
      onPaste={props.disablePaste ? handleDisablePaste : undefined}
      ref={props.inputRef}
      type={type}
      value={props.value}
    />
  );

  const fieldAndMask = (field: React.ReactElement) => {
    return props.mask ? (
      <NumberMask mask={props.mask}>{field}</NumberMask>
    ) : (
      field
    );
  };

  return (
    <div className={formGroupClasses}>
      <FormLabel
        errorMsg={props.errorMsg}
        example={props.example}
        hint={props.hint}
        inputId={inputId}
        optionalText={props.optionalText}
        small={props.smallLabel}
        labelClassName={props.labelClassName}
      >
        {props.label}
      </FormLabel>
      {fieldAndMask(field)}
    </div>
  );
}

export default InputText;
