import PropTypes from "prop-types";
import React from "react";
import uniqueId from "lodash/uniqueId";

/**
 * A checkbox or radio field. In most cases, you shouldn't use this
 * component directly. Instead, use `InputChoiceGroup` which renders
 * markup for the entire fieldset.
 *
 * [USWDS Reference ↗](https://designsystem.digital.gov/components/form-controls)
 */
function InputChoice({ type = "checkbox", ...props }) {
  // Generate a unique ID for associating the field with the label.
  // This is important for a11y.
  const inputId = uniqueId("InputChoice");

  return (
    <div className={`usa-${type}`}>
      <input
        checked={props.checked}
        className={`usa-${type}__input`}
        id={inputId}
        name={props.name}
        onChange={props.onChange}
        type={type}
        value={props.value}
      />
      <label className={`usa-${type}__label`} htmlFor={inputId}>
        {props.label}

        {props.hint && (
          <span className="usa-hint">
            <br />
            {props.hint}
          </span>
        )}
      </label>
    </div>
  );
}

InputChoice.propTypes = {
  /**
   * Sets the input's `checked` state. Use this in combination with `onChange`
   * for a controlled component.
   */
  checked: PropTypes.bool,
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
   * HTML input `type` attribute
   */
  type: PropTypes.oneOf(["checkbox", "radio"]),
  /**
   * Sets the input's `value`
   */
  value: PropTypes.oneOfType([PropTypes.number, PropTypes.string]).isRequired,
};

export default InputChoice;
