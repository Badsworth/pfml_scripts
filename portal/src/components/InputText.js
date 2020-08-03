import FormLabel from "./FormLabel";
import Mask from "./Mask";
import PropTypes from "prop-types";
import React from "react";
import classnames from "classnames";
import useUniqueId from "../hooks/useUniqueId";

/**
 * Text [input](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/input) field. Also renders
 * supporting UI elements like label, hint text, and error message.
 *
 * [USWDS Reference ↗](https://designsystem.digital.gov/components/form-controls)
 * Masked field functionality copied from [CMS design system](https://design.cms.gov/components/masked-field)
 */
function InputText({ type = "text", ...props }) {
  const inputId = useUniqueId("InputText");
  const hasError = !!props.errorMsg;

  const fieldClasses = classnames("usa-input", props.inputClassName, {
    "usa-input--error": hasError,
    [`usa-input--${props.width}`]: !!props.width,
  });
  const formGroupClasses = classnames(
    "usa-form-group",
    props.formGroupClassName,
    {
      "usa-form-group--error": hasError,
    }
  );

  const field = (
    <input
      autoComplete={props.autoComplete}
      className={fieldClasses}
      id={inputId}
      inputMode={props.inputMode}
      pattern={props.pattern}
      maxLength={props.maxLength}
      name={props.name}
      onBlur={props.onBlur}
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
        inputId={inputId}
        hint={props.hint}
        optionalText={props.optionalText}
        small={props.smallLabel}
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
   * HTML input `inputmode` attribute
   */
  inputMode: PropTypes.string,
  /**
   * Add a `ref` to the input element
   */
  inputRef: PropTypes.object,
  /**
   * Localized field label
   */
  label: PropTypes.node.isRequired,
  /**
   * Apply formatting to the field that's unique to the value
   * you expect to be entered. Depending on the mask, the
   * field's appearance and functionality may be affected.
   */
  mask: PropTypes.oneOf(["currency", "ssn", "fein"]),
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
   * HTML input `onChange` attribute
   */
  onChange: PropTypes.func,
  /**
   * Localized text indicating this field is optional
   */
  optionalText: PropTypes.node,
  /**
   * HTML input `pattern` attribute
   */
  pattern: PropTypes.string,
  /**
   * Enable the smaller label variant
   */
  smallLabel: PropTypes.bool,
  /**
   * HTML input `type` attribute
   */
  type: PropTypes.string,
  /**
   * Change the width of the input field
   */
  width: PropTypes.oneOf(["small", "medium"]),
  /**
   * Sets the input's `value`. Use this in combination with `onChange`
   * for a controlled component.
   */
  value: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
};

export default InputText;
