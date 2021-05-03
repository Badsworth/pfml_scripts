import FormLabel from "./FormLabel";
import PropTypes from "prop-types";
import React from "react";
import classnames from "classnames";
import useUniqueId from "../hooks/useUniqueId";

/**
 * A dropdown (`select`) allows users to select one option from a temporary modal menu.
 * Also renders supporting UI elements like a `label`, hint text, and error message.
 *
 * [USWDS Reference ↗](https://designsystem.digital.gov/components/form-controls/#dropdown)
 */
function Dropdown(props) {
  const hasError = !!props.errorMsg;
  const inputId = useUniqueId("Dropdown");

  const fieldClasses = classnames(
    "usa-select maxw-mobile-lg",
    props.selectClassName,
    {
      "usa-input--error": hasError,
    }
  );

  const formGroupClasses = classnames(
    "usa-form-group",
    props.formGroupClassName,
    {
      "usa-form-group--error": hasError,
    }
  );

  return (
    <div className={formGroupClasses}>
      <FormLabel
        errorMsg={props.errorMsg}
        hint={props.hint}
        inputId={inputId}
        optionalText={props.optionalText}
        small={props.smallLabel}
        labelClassName={props.labelClassName}
      >
        {props.label}
      </FormLabel>

      <select
        className={fieldClasses}
        id={inputId}
        name={props.name}
        onChange={props.onChange}
        value={props.value}
        disabled={props.disabled ? "disabled" : false}
      >
        {/* Include a blank initial option which will be chosen if no option has been selected yet */}
        {!props.hideEmptyChoice && (
          <option value="">{props.emptyChoiceLabel}</option>
        )}

        {props.choices.map((choice) => (
          <option key={choice.value} value={choice.value}>
            {choice.label}
          </option>
        ))}
      </select>
    </div>
  );
}

Dropdown.propTypes = {
  /**
   * List of choices to be rendered in the dropdown
   */
  choices: PropTypes.arrayOf(
    PropTypes.shape({
      label: PropTypes.oneOfType([PropTypes.number, PropTypes.string])
        .isRequired,
      value: PropTypes.oneOfType([PropTypes.number, PropTypes.string])
        .isRequired,
    })
  ).isRequired,
  /**
   * Whether the select is not ready to receive user input
   */
  disabled: PropTypes.bool,
  /**
   * Localized label for the initially selected option when no value is set
   */
  emptyChoiceLabel: PropTypes.string,
  /**
   * Localized error message. Setting this enables the error state styling.
   */
  errorMsg: PropTypes.node,
  /**
   * Localized hint text
   */
  hint: PropTypes.node,
  /**
   * Additional classes to include on the HTML select
   */
  selectClassName: PropTypes.string,
  /**
   * Override the label's default text-bold class
   */
  labelClassName: PropTypes.string,
  /**
   * Additional classes to include on the containing form group element
   */
  formGroupClassName: PropTypes.string,
  /**
   * Localized label
   */
  label: PropTypes.node.isRequired,
  /**
   * HTML input `name` attribute
   */
  name: PropTypes.string.isRequired,
  /**
   * Localized text indicating this field is optional
   */
  optionalText: PropTypes.node,
  /**
   * HTML input `onChange` attribute
   */
  onChange: PropTypes.func,
  /**
   * Enable the smaller label variant
   */
  smallLabel: PropTypes.bool,
  /**
   * Flag to hide empty choice as first option
   */
  hideEmptyChoice: PropTypes.bool,
  /** The `value` of the selected choice */
  value: PropTypes.oneOfType([PropTypes.number, PropTypes.string]),
};

export default Dropdown;
