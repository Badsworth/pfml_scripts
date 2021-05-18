import FormLabel from "./FormLabel";
import Mask from "./Mask";
import PropTypes from "prop-types";
import React from "react";
import classnames from "classnames";
import usePiiHandlers from "../hooks/usePiiHandlers";
import useUniqueId from "../hooks/useUniqueId";

/**
 * Text [input](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/input) field. Also renders
 * supporting UI elements like label, hint text, and error message.
 *
 * [USWDS Reference ↗](https://designsystem.digital.gov/components/form-controls)
 * Masked field functionality copied from [CMS design system](https://design.cms.gov/components/masked-field)
 */
function InputText({ type = "text", ...props }) {
  let inputId = useUniqueId("InputText");
  inputId = props.inputId || inputId;

  const hasError = !!props.errorMsg;
  let inputMode = props.inputMode;

  if (type === "number") {
    // Prevent usage of type="number"
    // See: https://css-tricks.com/you-probably-dont-need-input-typenumber/
    type = "text";
    inputMode = "numeric";
  }

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

  const { handleFocus, handleBlur } = usePiiHandlers(props);

  const field = (
    <input
      autoComplete={props.autoComplete}
      aria-labelledby={`${inputId}_label ${inputId}_hint`}
      className={fieldClasses}
      data-value-type={props.valueType}
      id={inputId}
      inputMode={inputMode}
      maxLength={props.maxLength}
      name={props.name}
      onBlur={props.pii ? handleBlur : props.onBlur}
      onFocus={props.pii ? handleFocus : props.onFocus}
      onChange={props.onChange}
      ref={props.inputRef}
      type={type}
      value={props.value}
    />
  );

  const fieldAndMask = (field) => {
    return props.mask ? <Mask mask={props.mask}>{field}</Mask> : field;
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

InputText.propTypes = {
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
   * HTML input `inputmode` attribute. Defaults to "text". Browsers
   * use this attribute to inform the type of keyboard displayed
   * to the user.
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
  mask: PropTypes.oneOf(["currency", "fein", "hours", "phone", "ssn", "zip"]),
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
   * HTML input `type` attribute. Defaults to "text".
   */
  type: PropTypes.oneOf(["email", "password", "tel", "text"]),
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
   * Adds a data attribute to the input. Can be used by
   * change handlers or `getInputValueFromEvent` to inform
   * what value type the field should be converted to before
   * saving it back to the API.
   */
  valueType: PropTypes.oneOf(["integer", "float", "string"]),
};

export default InputText;
