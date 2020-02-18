import FormLabel from "./FormLabel";
import PropTypes from "prop-types";
import React from "react";
import classnames from "classnames";
import uniqueId from "lodash/uniqueId";

/**
 * Text [input](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/input) field. Also renders
 * supporting UI elements like label, hint text, and error message.
 *
 * [USWDS Reference ↗](https://designsystem.digital.gov/components/form-controls)
 */
function InputText({ type = "text", ...props }) {
  // Generate a unique ID for associating field elements like the
  // input, label, and error message. This is important for a11y.
  const inputId = uniqueId("InputText");
  const hasError = !!props.errorMsg;

  const fieldClasses = classnames("usa-input", {
    "usa-input--error": hasError,
    [`usa-input--${props.width}`]: !!props.width
  });
  const formGroupClasses = classnames("usa-form-group", {
    "usa-form-group--error": hasError
  });

  return (
    <div className={formGroupClasses}>
      <FormLabel
        errorMsg={props.errorMsg}
        inputId={inputId}
        hint={props.hint}
        optionalText={props.optionalText}
      >
        {props.label}
      </FormLabel>

      <input
        className={fieldClasses}
        id={inputId}
        name={props.name}
        onChange={props.onChange}
        type={type}
        value={props.value}
      />
    </div>
  );
}

InputText.propTypes = {
  /**
   * Localized error message. Setting this enables the error state styling.
   */
  errorMsg: PropTypes.node,
  /**
   * Localized hint text
   */
  hint: PropTypes.node,
  /**
   * Localized field label
   */
  label: PropTypes.node.isRequired,
  /**
   * HTML input `name` attribute
   */
  name: PropTypes.string.isRequired,
  /**
   * HTML input `onChange` attribute
   */
  onChange: PropTypes.func,
  /**
   * Localized text indicating this field is optional
   */
  optionalText: PropTypes.node,
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
  value: PropTypes.oneOfType([PropTypes.string, PropTypes.number])
};

export default InputText;
