import FormLabel from "./FormLabel";
import InputChoice from "./InputChoice";
import PropTypes from "prop-types";
import React from "react";
import classnames from "classnames";

/**
 * A grouping of checkbox or radio fields. Also renders supporting UI
 * elements like a `legend`, hint text, and error message.
 *
 * [USWDS Reference ↗](https://designsystem.digital.gov/components/form-controls)
 */
function InputChoiceGroup({ type = "checkbox", ...props }) {
  const hasError = !!props.errorMsg;

  const formGroupClasses = classnames("usa-fieldset", "usa-form-group", {
    "usa-form-group--error": hasError,
  });

  return (
    <fieldset className={formGroupClasses}>
      <FormLabel
        component="legend"
        errorMsg={props.errorMsg}
        hint={props.hint}
        optionalText={props.optionalText}
      >
        {props.label}
      </FormLabel>

      <div className="margin-top-3">
        {props.choices.map((choice) => (
          <InputChoice
            key={choice.value}
            name={props.name}
            onChange={props.onChange}
            type={type}
            {...choice}
          />
        ))}
      </div>
    </fieldset>
  );
}

InputChoiceGroup.propTypes = {
  /**
   * List of choices to be rendered as individual checkbox/radio fields.
   */
  choices: PropTypes.arrayOf(
    PropTypes.shape({
      checked: PropTypes.bool,
      hint: PropTypes.node,
      label: PropTypes.node.isRequired,
      value: PropTypes.oneOfType([PropTypes.number, PropTypes.string])
        .isRequired,
    })
  ).isRequired,
  /**
   * Localized error message. Setting this enables the error state styling.
   */
  errorMsg: PropTypes.node,
  /**
   * Localized hint text for the entire fieldset
   */
  hint: PropTypes.node,
  /**
   * Localized label for the entire fieldset
   */
  label: PropTypes.node.isRequired,
  /**
   * HTML input `name` attribute applied to each choice in the list
   */
  name: PropTypes.string.isRequired,
  /**
   * Localized text indicating this fieldset is optional
   */
  optionalText: PropTypes.node,
  /**
   * HTML input `onChange` attribute applied to each choice in the list
   */
  onChange: PropTypes.func,
  /**
   * HTML input `type` attribute applied to each choice in the list
   */
  type: PropTypes.oneOf(["checkbox", "radio"]),
};

export default InputChoiceGroup;
